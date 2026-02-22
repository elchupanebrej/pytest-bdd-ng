# Feature: HTTP feature loading
  This feature documents loading Gherkin feature files over HTTP and executing
  scenarios as regular pytest tests, including explicit URL mode and
  base-URL resolution mode.

## Scenario: Load feature from explicit HTTP URL
* Given Localserver endpoint "/feature" responding content:

    ```gherkin
    Feature: minimal
      Scenario: Passing cukes
        Given I have 42 cukes in my belly
    ```

* And File "test_http.py" with fixture templated content:

    ```python
    from pytest_bdd import given, scenarios, FeaturePathType
    from pytest_bdd.mimetype import Mimetype

    @given("I have 42 cukes in my belly")
    def _results():
      pass

    test_cukes = scenarios(
      "http://localhost:{httpserver_port}/feature",
      features_mimetype=Mimetype.gherkin_plain,
      features_path_type=FeaturePathType.URL,
    )
    ```

* When run pytest

    | cli_args | -k | test_http.py |
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Load feature using HTTP base URL from pytest.ini
* Given Localserver endpoint "/feature" responding content:

    ```gherkin
    Feature: minimal
      Scenario: Passing cukes
        Given I have 42 cukes in my belly
    ```

* And File "test_http.py" with fixture templated content:

    ```python
    from pytest_bdd import scenarios
    from pytest_bdd import given

    @given("I have 42 cukes in my belly")
    def _results():
      pass

    test_cukes = scenarios(
      "/feature",
      features_base_url="http://localhost:{httpserver_port}",
    )
    ```

* When run pytest

    | cli_args | -k | test_http.py |
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Load feature URL from Windows shortcut file
* Given Localserver endpoint "/feature" responding content:

    ```gherkin
    Feature: minimal
      Scenario: Passing cukes
        Given I have 42 cukes in my belly
    ```

* And File "test_http.url" with fixture templated content:

    ```ini
    [InternetShortcut]
    URL=http://localhost:{httpserver_port}/feature
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given

    @given("I have 42 cukes in my belly")
    def _results():
      pass
    ```

* And File "test_http.py" with content:

    ```python
    from configparser import ConfigParser

    from pytest_bdd import FeaturePathType, scenarios
    from pytest_bdd.mimetype import Mimetype

    parser = ConfigParser()
    parser.read("test_http.url")
    url = parser["InternetShortcut"]["URL"]

    test_http = scenarios(
      url,
      features_mimetype=Mimetype.gherkin_plain,
      features_path_type=FeaturePathType.URL,
    )
    ```

* When run pytest

    | cli_args | -k | test_http.py |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Load feature URL from freedesktop desktop link
* Given Localserver endpoint "/feature" responding content:

    ```gherkin
    Feature: minimal
      Scenario: Passing cukes
        Given I have 42 cukes in my belly
    ```

* And File "test_http.desktop" with fixture templated content:

    ```ini
    [Desktop Entry]
    Type=Link
    URL=http://localhost:{httpserver_port}/feature
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given

    @given("I have 42 cukes in my belly")
    def _results():
      pass
    ```

* And File "test_http.py" with content:

    ```python
    from configparser import ConfigParser

    from pytest_bdd import FeaturePathType, scenarios
    from pytest_bdd.mimetype import Mimetype

    parser = ConfigParser()
    parser.read("test_http.desktop")
    url = parser["Desktop Entry"]["URL"]

    test_http = scenarios(
      url,
      features_mimetype=Mimetype.gherkin_plain,
      features_path_type=FeaturePathType.URL,
    )
    ```

* When run pytest

    | cli_args | -k | test_http.py |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Load feature URL from macOS webloc file
* Given Localserver endpoint "/feature" responding content:

    ```gherkin
    Feature: minimal
      Scenario: Passing cukes
        Given I have 42 cukes in my belly
    ```

* And File "conftest.py" with fixture templated content:

    ```python
    from pathlib import Path

    from pytest_bdd import given
    from pytest_bdd.util.webloc import write as webloc_write

    webloc_write(Path("test_http.webloc"), "http://localhost:{httpserver_port}/feature")

    @given("I have 42 cukes in my belly")
    def _results():
      pass

    ```

* And File "test_http.py" with content:

    ```python
    import plistlib
    from pathlib import Path

    from pytest_bdd import FeaturePathType, scenarios
    from pytest_bdd.mimetype import Mimetype

    with Path("test_http.webloc").open("rb") as f:
      url = plistlib.load(f)["URL"]

    test_http = scenarios(
      url,
      features_mimetype=Mimetype.gherkin_plain,
      features_path_type=FeaturePathType.URL,
    )
    ```

* When run pytest

    | cli_args | -k | test_http.py |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Load StructBDD document from explicit HTTP URL
* Given Localserver endpoint "/feature" responding content:

    ```yaml
    Name: minimal
    Steps:
      - Step:
          Name: Passing cukes
          Steps:
            - Given: I have 42 cukes in my belly
    ```

* And File "test_http.py" with fixture templated content:

    ```python
    import pytest
    from pytest_bdd import given, scenarios, FeaturePathType
    from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
    from pytest_bdd.mimetype import Mimetype

    pytestmark = [pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")]

    @given("I have 42 cukes in my belly")
    def _results():
      pass

    test_cukes = scenarios(
      "http://localhost:{httpserver_port}/feature",
      features_mimetype=Mimetype.struct_bdd_yaml,
      features_path_type=FeaturePathType.URL,
    )
    ```

* When run pytest

    | subprocess | true |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
