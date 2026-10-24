Feature: External CSV and TSV Examples sources
''''''''''''''''''''''''''''''''''''''''''''''

Scenario outlines can load their examples table from a separate file
while retaining the source feature identity in reports.

Use ``Examples: table: users.csv``, ``Examples: <table:users.csv>``,
``Examples: | table: users.csv |``, or a one-cell
``| table: users.csv |`` row below ``Examples:``. Paths resolve from the
referencing feature, and ``.tsv``/``.tab`` files use tabs. UTF-8 BOMs
and CRLF are supported. Missing, unreadable, empty, invalidly encoded,
or malformed tables fail collection with the feature marker and resolved
source path in the diagnostic. CSV quoting, empty cells, commas, pipes,
backslashes, and multiline values are preserved through Gherkin
escaping. Source files remain unchanged and are reread on each pytest
session. Generated Examples table rows have unknown Gherkin source
lines; source reports retain the marker and physical dataset row
locations separately. This checkout has no batch collector yet.

Scenario: The installed public facade loads autoloaded and explicitly bound sources


-  Given the pytest-cuke wheel built from this checkout is installed in
   a fresh consumer project

-  And consumer file "conftest.py" contains:

   ::

      from pytest_cuke import given, parsers, then

      @given("the user lookup service is ready", target_fixture="lookup_ready")
      def lookup_service():
          return True

      @given(parsers.parse("user row {name} has tier {tier}"), target_fixture="user_record")
      def load_user(lookup_ready, name, tier):
          assert lookup_ready
          return {"name": name, "tier": tier}

      @then(parsers.parse("looked up user {name} has tier {tier}"))
      def check_user(user_record, name, tier):
          assert user_record == {"name": name, "tier": tier}

      @given("the report session is open", target_fixture="report_session")
      def open_report_session():
          return True

      @given(parsers.parse("the report row is {name}"), target_fixture="report_row")
      def load_report_row(report_session, name):
          assert report_session
          return name

      @then(parsers.parse("the report row result is {expected}"))
      def check_report_row(report_row, expected):
          assert report_row == expected

-  And consumer file "features/users.csv" contains:

   ::

      name,tier
      Ada,gold
      Grace,silver

-  And consumer file "features/users.feature" contains:

   ::

      Feature: External users
        Background:
          Given the user lookup service is ready

        Scenario Outline: Look up an external user
          Given user row <name> has tier <tier>
          Then looked up user <name> has tier <tier>

            Examples: | table: users.csv |

-  And consumer file "features/inline-users.feature" contains:

   ::

      Feature: Inline users
        Background:
          Given the user lookup service is ready

        Scenario Outline: Look up an inline user
          Given user row <name> has tier <tier>
          Then looked up user <name> has tier <tier>

          Examples:
            | name  | tier   |
            | Ada   | gold   |
            | Grace | silver |

-  And consumer file "features/markdown-users.tab" contains UTF-8 BOM
   and CRLF:

   ::

      name\ttier
      Tina\tbronze
      Maja\tcopper

-  And consumer file "features/markdown-users.feature.md" contains:

   ::

      # Feature: External Markdown users
      ## Scenario Outline: Look up a Markdown user
        * Given the lookup service is ready
        * Given user row <name> has tier <tier>
        * Then looked up user <name> has tier <tier>
      ### Examples:
          | table: markdown-users.tab |

-  And consumer file "features/report-users.csv" contains:

   ::

      name,expected
      passed,passed
      failed,expected-other

-  And consumer file "features/reported-users.feature" contains:

   ::

      Feature: External rows in reports
        Background:
          Given the report session is open

        Scenario Outline: Report an external row outcome
          Given the report row is <name>
          Then the report row result is <expected>

          Examples: <table:report-users.csv>

-  When I run installed pytest with arguments "--rootdir=.
   --cuke-json=report.json --cuke-messages-ndjson=messages.ndjson
   --cuke-progress"

-  Then pytest should exit with a non-zero code

-  And consumer reports should preserve external row identities, source
   URIs, Background steps, and outcomes

Scenario: Invalid external sources fail collection with both paths


-  Given the pytest-cuke wheel built from this checkout is installed in
   a fresh consumer project

-  And consumer file "features/broken.csv" contains:

   ::

      name,tier
      Ada

-  And consumer file "features/broken.feature" contains:

   ::

      Feature: Invalid external examples
        Scenario Outline: Read an invalid source
          Given user row <name> has tier <tier>

          Examples: table: broken.csv

-  When I run installed pytest with arguments "--rootdir=.
   --cuke-autoload"

-  Then pytest should exit with a non-zero code

-  And pytest output should identify the invalid external Examples row
   and both paths

Scenario: Explicit bindings and subsequent sessions read current source rows


-  Given the pytest-cuke wheel built from this checkout is installed in
   a fresh consumer project

-  And consumer file "conftest.py" contains:

   ::

      from pytest_cuke import given, parsers, then

      @given("the user lookup service is ready", target_fixture="lookup_ready")
      def lookup_service():
          return True

      @given(parsers.parse("user row {name} has tier {tier}"), target_fixture="user_record")
      def load_user(lookup_ready, name, tier):
          assert lookup_ready
          return {"name": name, "tier": tier}

      @then(parsers.parse("looked up user {name} has tier {tier}"))
      def check_user(user_record, name, tier):
          assert user_record == {"name": name, "tier": tier}

-  And consumer file "features/users.csv" contains:

   ::

      name,tier
      Ada,gold
      Grace,silver

-  And consumer file "features/users.feature" contains:

   ::

      Feature: External users
        Background:
          Given the user lookup service is ready

        Scenario Outline: Look up an external user
          Given user row <name> has tier <tier>
          Then looked up user <name> has tier <tier>

          Examples: table: users.csv

-  When consumer file "test_explicit_binding.py" contains:

   ::

      from pytest_cuke import scenario

      @scenario("users.feature")
      def test_explicit_users_binding():
          pass

-  And I run installed pytest with arguments "--rootdir=.
   --cuke-no-autoload"

-  Then pytest should exit with code 0

-  And the test outcome should have 2 passed scenarios

-  When consumer file "features/users.csv" contains:

   ::

      name,tier
      Lin,platinum

-  And I run installed pytest with arguments "--rootdir=.
   --cuke-no-autoload"

-  Then pytest should exit with code 0

-  And the test outcome should have 1 passed scenarios
