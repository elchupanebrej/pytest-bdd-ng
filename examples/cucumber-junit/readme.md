# Cucumber JUnit XML example

This standalone consumer uses pytest-cuke's public step decorators and autoloads
the `.feature` file from `features/`. The feature demonstrates feature and Rule
backgrounds, a doc string, a data table, an outline, descriptions, and tags.

Install pytest-cuke, Node.js, and the pinned official formatter, then run the
feature from this directory:

```sh
python -m pip install 'pytest-cuke>=2.3.1'
npm install --no-save --no-package-lock '@cucumber/junit-xml-formatter@0.14.1'
python -m pytest --cuke-junit=report.xml -q
```

The E2E suite copies this project into a fresh installed consumer and inspects
the emitted XML. It also compares live output with standalone replay from the
same Cucumber Messages stream.
