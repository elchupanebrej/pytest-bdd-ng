# Cucumber Summary example

This consumer project uses pytest-cuke's public step decorators and autoloads
the kebab-case feature under `features/`. Its outline executes two scenarios;
the Background and two steps in each row give the official summary six passing
steps.

Install pytest-cuke, Node.js, and the pinned official Cucumber formatter, then
run the feature from this directory:

```sh
python -m pip install 'pytest-cuke>=2.3.1'
npm install --no-save --no-package-lock '@cucumber/cucumber@13.3.0'
python -m pytest --cuke-parser=python --cuke-summary -q
```

The summary reports the two scenario outline rows, their step outcomes, and
the run duration. The E2E suite copies this project into a fresh installed
consumer and checks the real formatter output.
