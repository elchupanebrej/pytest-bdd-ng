Tag and mark hook expressions
=============================

Tag hooks and mark hooks use different expression languages. This preserves
their original consumer contracts after the ``pytest_cuke`` namespace migration.

``before_tag``, ``after_tag`` and ``around_tag`` match source tag names exactly.
For a feature tagged ``@smoke``, use ``@smoke`` in the expression. The expression
``smoke`` does not match that source tag. The named ``GherkinTagExpression``
class follows the same rule and reports invalid Cucumber expressions as
``ValueError``.

``before_mark``, ``after_mark`` and ``around_mark`` use the installed pytest
mark-expression grammar. Use ``smoke`` for ``pytest.mark.smoke``; ``@smoke`` is
invalid syntax. Keyword arguments in mark expressions follow pytest's support
and are available from pytest 8.3. Invalid expressions fail fixture setup before
the hook body runs. Older pytest ``ParseError`` is translated to ``ValueError``;
modern pytest's ``SyntaxError`` is preserved.

The generic ``TagExpression`` and ``parse_tag_expression`` API continue to
normalize names with and without ``@``. Use that API when normalization is
intended. The named ``GherkinTagExpression`` and ``MarksTagExpression`` classes
are distinct implementations; they are no longer aliases of the generic class.
