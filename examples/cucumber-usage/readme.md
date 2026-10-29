# Cucumber Usage example

This consumer project uses pytest-cuke's public step decorators and autoloads
the kebab-case feature under `features/`. Its outline produces two matches for
each interpolated step definition. The step module also has one unused
definition so the report demonstrates Cucumber's `UNUSED` entry.

Install pytest-cuke, Node.js, and the pinned official formatter, then run the
feature from this directory:

```sh
python -m pip install 'pytest-cuke>=2.3.1'
npm install --no-save --no-package-lock '@cucumber/cucumber@13.3.0'
python -m pytest --cuke-parser=python --cuke-usage -q
```

The terminal report includes definition patterns and source locations, match
examples, and available durations. The E2E suite copies this project into a
fresh installed consumer and verifies the report against the emitted Messages
stream.
