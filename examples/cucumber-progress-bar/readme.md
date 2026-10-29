# Cucumber progress-bar example

This consumer project uses pytest-cuke's public step decorator and autoloads
the kebab-case feature under `features/`. Its two scenarios pass, so the
progress bar counts both completed Pickles.

Install pytest-cuke, Node.js, and the pinned official formatter, then run the
feature from this directory:

```sh
python -m pip install 'pytest-cuke>=2.3.1'
npm install --no-save --no-package-lock '@cucumber/pretty-formatter@4.0.2'
python -m pytest --cuke-parser=python --cuke-progress-bar -q
```

In a terminal, pytest-cuke redraws a width-aware progress bar. When output is
piped, it prints one readable status marker per completed scenario.
