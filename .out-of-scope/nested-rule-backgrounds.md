# Nested Rule Backgrounds

The product will not add recursive `Rule` nesting or background inheritance through nested rules unless the official Gherkin specification adopts that structure.

## Why this is out of scope

Gherkin `Rule` elements are top-level children of a `Feature`; indentation does not define a nested rule hierarchy. The upstream report [cucumber/gherkin#126](https://github.com/cucumber/gherkin/issues/126) was closed as “not a bug” after its reporter confirmed that nested rules are not supported. Its maintainers described rules as top-level and pointed to a separate documentation issue for clarifying the behavior.

Implementing recursive Rule backgrounds here would add product-specific syntax and semantics to the Gherkin model, including inheritance and conflict rules that the upstream format does not define. The parser therefore supports feature backgrounds and top-level Rule backgrounds, including their merge order, but does not treat a Rule inside a Rule as a child.

If Gherkin later specifies nested rules, this decision can be revisited against that specification and its compatibility tests.

## Prior requests

- #105: “Fixup nested rules backgrounds”
