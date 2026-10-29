# Cucumber Usage JSON example

This small consumer project uses pytest-cuke's public step decorators and
autoloads the kebab-case feature under `features/`. Its outline produces two
matches for each interpolated step definition. The step module also has one
unused definition so the output demonstrates that the Cucumber formatter
reports discovered definitions with an empty `matches` array.

Install pytest-cuke, Node.js, and the pinned official formatter, then run the
feature from this directory:

```sh
python -m pip install 'pytest-cuke>=2.3.1'
npm install --no-save --no-package-lock '@cucumber/cucumber@13.3.0'
python -m pytest --cuke-parser=python --cuke-usage-json=usage.json -q
```

`usage.json` is the JSON array emitted by the pinned Cucumber Usage JSON
formatter. It contains definition locations, match locations and text, and
available durations; the values are not formatted for terminal display.
