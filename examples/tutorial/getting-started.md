# Standalone pytest-cuke library example

This small project demonstrates a searchable book catalog. Its feature file is
collected automatically, and its step definitions use the public `pytest_cuke`
facade.

Install the example dependencies and run it from this directory:

```sh
python -m pip install -r requirements.txt
python -m pytest
```

The project configuration uses `cuke_*` pytest settings. There is no mirror
`test_*.py` file for the feature.
