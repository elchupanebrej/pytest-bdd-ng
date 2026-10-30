Bind scenarios without generating steps
======================================

Use ``cuke generate steps --feature features/example.feature --target test_example.py --bind-only``
to add missing scenario bindings to an existing Python module without adding step
functions. The target must exist and contain valid Python. Existing user code is
preserved, and repeating the command leaves an already bound module unchanged.
Use ``--preview`` to inspect the proposed changes without writing the target.

``--bind-scenarios`` retains its combined behavior: it adds missing bindings and
missing step definitions. With ``--bind-only``, step generation is disabled even
if ``--bind-scenarios`` is also supplied. Success returns 0; rejected requests
return 2, including ``--bind-only`` without ``--target``. This additive workflow
restores the former binding-only capability using the current CLI namespace;
it does not restore the former exit code 100.

Binding-only collection reads the project's pytest configuration and feature-root
setting without setting up runtime fixtures or matching step definitions. In
particular, autouse fixtures do not run. Target imports and collection hooks
still execute as part of discovering existing bindings.
