# StructBDD format discovery

This standalone example defines the same runnable scenario in each supported
StructBDD file format. Pytest autoloads the files from `features/`, selects the
parser from each complete suffix, and runs the steps defined under `tests/`.

The supported suffixes are `.bdd` (YAML), `.bdd.yaml`, `.bdd.yml`, `.bdd.hocon`,
`.bdd.json5`, `.bdd.json`, `.bdd.hjson`, and `.bdd.toml`. Ordinary `.yaml` and
`.json` files are data files; autoload does not treat them as features.

From this checkout, install the project and its optional format loaders, then
run the example:

```sh
python -m pip install -e "../../.[struct-bdd]"
python -m pytest
```

## Select the features in different ways

The configured autoload run and an explicit pytest file list select the same
eight feature files:

```sh
python -m pytest --cuke-autoload --cuke-features-dir=features features
python -m pytest --cuke-autoload --cuke-features-dir=features \
  features/example.bdd \
  features/example.bdd.yaml \
  features/example.bdd.yml \
  features/example.bdd.hocon \
  features/example.bdd.json5 \
  features/example.bdd.json \
  features/example.bdd.hjson \
  features/example.bdd.toml
```

An existing test can use the recursive or explicit-file locator directly when
autoload is disabled:

```python
from pytest_cuke import scenario, scenarios


@scenarios(".", return_test_decorator=True)
def test_features_from_directory(feature, scenario):
    assert feature.name and scenario.name


@scenario("example.bdd.json5", "A JSON5 file is collected")
def test_one_explicit_feature(feature):
    assert feature.name == "StructBDD formats"
```

Run such decorator-bound tests with `--cuke-no-autoload` to avoid collecting
the same files a second time.

To install a released `pytest-cuke` package instead, install this example's
requirements and run the same pytest command:

```sh
python -m pip install -r requirements.txt
python -m pytest
```
