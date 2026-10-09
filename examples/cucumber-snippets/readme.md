# Cucumber snippets example

This consumer project uses pytest-cuke's public step decorators and autoloads
the kebab-case feature under `features/`. Each of its three scenarios has one
undefined Given, When, or Then step, so pytest reports suggestions for all
three keywords. The passing Background step is omitted from suggestions.
Generated JavaScript bindings use quoted-string and numeric parameter types.

Install pytest-cuke, Node.js, and the pinned official Cucumber formatter, then
run the feature from this directory:

```sh
python -m pip install 'pytest-cuke>=2.3.1'
npm install --no-save --no-package-lock '@cucumber/cucumber@13.3.0'
python -m pytest --cuke-parser=python --cuke-snippets -q
```

Pytest exits with an undefined-step failure after printing the suggestions.
That failure is expected: the formatter proposes bindings but does not add
them to the project.
