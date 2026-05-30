Cucumber Formatter Runtime Architecture
=======================================

Why This Exists
---------------

``pytest-bdd-ng`` exposes formatter options such as ``--cucumber-html``,
``--cucumber-pretty``, ``--cucumber-progress``, and ``--cucumber-junit`` from
Python, but several of the actual formatter implementations live in the
JavaScript ``cucumber`` ecosystem.

This note explains why the project does not call those upstream libraries
"directly", why the bridge uses rendered JavaScript templates, and what role
each template plays in the end-to-end flow.

User-Facing Flow
----------------

From a library user's point of view the formatter flow is:

1. A pytest run requests one or more cucumber formatter options.
2. The formatter plugins normalize those requests into a canonical runtime plan.
3. ``gherkin_message_reporter`` emits one canonical cucumber envelope stream for
   the run.
4. If the request targets a JavaScript formatter, the reporter materializes the
   required runtime assets into a temporary directory and starts Node.js.
5. The Node runtime consumes the same live envelope stream that the Python
   reporter owns.
6. The formatter writes live terminal output, files, or both, depending on the
   selected formatter.

The same architectural boundary is reused for standalone replay:

1. ``pytest`` produces canonical ``messages.ndjson``.
2. ``pytest_bdd.script.render_cucumber_formatters`` builds the same formatter
   runtime plan.
3. A first-class standalone rendering service resolves formatter requests from
   the standalone formatter catalog and replays envelopes from disk instead of
   from the live pytest stream.

The important point for maintainers is that the project does not expose
"formatter plugins" as a separate execution model. There is one canonical
message stream, and every formatter integration must consume that stream rather
than inventing its own reporting path.

Why We Do Not Call Upstream Libraries Directly
----------------------------------------------

There are two different "directly" options that might look simpler but are not
good fits for this project.

Calling JavaScript libraries directly from Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is not a real option. The upstream formatters are JavaScript packages, so
Python still needs a Node.js boundary.

Calling the upstream formatter CLI as an opaque subprocess
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is possible in principle, but it is not sufficient for this runtime:

* ``pytest-bdd-ng`` owns the canonical cucumber envelope stream, not the
  upstream CLI.
* live terminal formatters must render incrementally during the pytest run,
  not only after a finished ``messages.ndjson`` file exists;
* ``pytest-xdist`` requires one controller-owned rendering authority, so worker
  processes must forward envelopes to the controller instead of each worker
  invoking its own formatter CLI;
* several upstream formatters do not share one stable public "feed me NDJSON
  and return output" contract;
* terminal ownership, TTY detection, output-path handling, temporary asset
  layout, and compatibility diagnostics must stay under pytest-bdd-ng control.

Because of those constraints, the project needs a small adapter runtime between
Python-owned reporting and upstream JavaScript formatter packages.

Architecture Boundary
---------------------

The runtime is intentionally split into three layers:

Python orchestration layer
~~~~~~~~~~~~~~~~~~~~~~~~~~

Python owns:

* the explicit lifecycle contract between the pytest entrypoint and the
  reporting runtime;
* reporter assembly and service wiring;
* formatter option parsing and request normalization;
* the canonical envelope stream;
* xdist controller and worker routing;
* temporary runtime directory management;
* Node process lifecycle and diagnostics.

The ``GherkinMessageReporter`` object is intentionally a narrow coordination
root. It owns shared state references and delegates assembly, transport,
lifecycle work, and formatter execution to dedicated collaborators. If a new
change pushes request resolution, service graph construction, or standalone
replay wiring back into ``plugin.py``, the architecture is regressing.

JavaScript bridge layer
~~~~~~~~~~~~~~~~~~~~~~~

The bridge owns:

* loading formatter adapters;
* creating output streams;
* feeding live or replayed envelopes into formatter adapters;
* finalizing formatter output when the run finishes.

Formatter adapter layer
~~~~~~~~~~~~~~~~~~~~~~~

Formatter-specific adapters own:

* formatter-specific request normalization;
* compatibility glue for upstream package loading;
* any formatter-specific event aggregation;
* output behaviors that cannot be described by plain metadata alone.

This split is why the repository keeps both one bridge template and a small set
of formatter-specific templates.

Template Roles
--------------

``live_formatter_bridge.mjs.j2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

File:
``src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/live_formatter_bridge.mjs.j2``

This is the main Node.js entrypoint rendered for every JavaScript-backed
formatter session.

Responsibilities:

* load the requested formatter runtime assets;
* initialize terminal and file streams;
* accept envelopes from stdin or from a replay file;
* route envelopes to all requested formatter adapters;
* close and flush outputs at the end of the session.

Why it exists:

* every JavaScript formatter run needs one orchestrator;
* the script is too large and too version-sensitive to keep inline in Python;
* the bridge must remain formatter-agnostic so the Python layer can reuse it
  for live rendering and standalone replay.

``formatter_adapter_support.cjs.j2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

File:
``src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatter_adapter_support.cjs.j2``

This is the shared compatibility library for formatter adapters.

Responsibilities:

* resolve formatter classes and helper modules from upstream packages;
* isolate unstable or package-specific import details in one place;
* provide shared rendering helpers used by multiple adapters.

Why it exists:

* without it, each adapter template would duplicate the same upstream
  compatibility glue;
* upstream package layouts are not stable enough to hardcode repeatedly across
  many small templates;
* keeping the compatibility layer shared makes it easier to update for upstream
  package changes.

``formatters/pretty.cjs.j2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

User-facing option: ``--cucumber-pretty``

Why it exists:

* the pretty formatter is backed by a separate upstream package and class
  contract;
* pytest-bdd-ng needs a stable adapter boundary instead of scattering those
  import details into Python metadata;
* the adapter keeps ``live_formatter_bridge`` free of package-specific logic.

``formatters/junit.cjs.j2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

User-facing option: ``--cucumber-junit``

Why it exists:

* the JUnit formatter has a distinct output lifecycle and package contract;
* it is not just "another terminal formatter";
* the adapter makes the XML printer behave like one participant in the common
  envelope-driven runtime.

``formatters/progress.cjs.j2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

User-facing option: ``--cucumber-progress``

Why it exists:

* progress output is derived from execution state, not just from forwarding
  envelopes into an upstream formatter object;
* pytest-bdd-ng needs deterministic per-attempt status mapping from the
  canonical envelope stream into progress characters;
* this behavior belongs in a formatter adapter, not in the bridge and not in
  Python.

``formatters/progress_bar.cjs.j2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

User-facing option: ``--cucumber-progress-bar``

Why it exists:

* progress-bar rendering is terminal-sensitive and stateful;
* it must track totals, completion, and fallback behavior for non-TTY outputs;
* those concerns are specific to this formatter style and should not complicate
  the shared bridge.

``formatters/usage.cjs.j2``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

User-facing option: ``--cucumber-usage``

Why it exists:

* usage output is an aggregated report built from support-code and execution
  data, not a direct passthrough formatter;
* it needs end-of-run computation over accumulated runtime information;
* that makes it adapter-specific logic instead of generic bridge logic.

Why Some Formatters Do Not Have Their Own Template
--------------------------------------------------

Not every formatter needs a dedicated adapter template.

At the time of writing, ``summary``, ``json``, ``snippets``, and
``usage-json`` can be represented through stable runtime metadata and the
shared bridge contract without additional JavaScript behavior.

The rule is:

* if a formatter can be described by stable metadata plus the shared bridge
  contract, do not create a dedicated template;
* if a formatter needs package-specific compatibility glue, stateful
  aggregation, TTY-aware behavior, or a non-uniform lifecycle, give it a
  dedicated adapter template.

Maintenance Rules
-----------------

When maintaining this subsystem:

* keep Python responsible for envelope ownership, process orchestration, and
  pytest or xdist integration;
* keep the entrypoint talking to the runtime only through the explicit public
  lifecycle contract;
* keep standalone replay on the standalone rendering service boundary rather
  than rebuilding fake pytest ``Config`` or pluginmanager objects;
* keep ``live_formatter_bridge`` responsible for shared JavaScript runtime
  orchestration only;
* keep formatter-specific request-building and runtime-asset quirks in
  formatter plugins or formatter adapter templates rather than pushing them
  into the shared bridge or one monolithic Python base class;
* keep formatter discovery on one canonical source per execution mode:
  pytest11 plus hooks for live pytest runs, and the explicit standalone
  formatter catalog for replay;
* prefer shared helper expansion in
  ``formatter_adapter_support.cjs.j2`` over copy-pasting upstream glue into
  multiple adapter templates;
* do not inline long generated scripts back into Python string literals;
* do not add a new formatter template unless the shared bridge plus metadata is
  genuinely insufficient.

Review Checklist for New Formatter Integrations
-----------------------------------------------

When adding or changing a formatter integration, confirm:

* the formatter still consumes the canonical envelope stream rather than a
  private reporting path;
* controller-owned rendering remains the only rendering authority in xdist
  runs;
* the integration really needs custom JavaScript behavior before introducing a
  new template;
* any upstream package compatibility logic is isolated to the adapter or shared
  adapter support layer, not smeared across Python orchestration code.
