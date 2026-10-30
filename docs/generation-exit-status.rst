Generation exit status
======================

The standalone ``cuke generate steps`` command defaults to ``--exit-status=current``:
success returns 0 whether the target changes or not, and handled generation errors
return 2.

Automation that needs the historical change signal can opt into
``--exit-status=legacy100``. This mode returns:

* 100 when Python additions are printed, a target changes, or preview finds changes;
* 0 when no additions are needed;
* 100 for handled generation errors, including an invalid or missing target.

For example::

    cuke generate steps --feature features/example.feature --target test_example.py --exit-status=legacy100

The option changes only the exit code. Transactional validation, preview, error
messages, and target protection are preserved. Argument-parser errors, such as
an unknown option, invalid choice, or omitted required ``--feature``, still return
usage status 2 before generation begins. Interrupted processes and unexpected
internal exceptions are outside this exit-policy contract.

This option restores a historical automation capability in the current CLI
namespace. It does not change the default policy or introduce exit code 100 into
ordinary pytest test execution.
