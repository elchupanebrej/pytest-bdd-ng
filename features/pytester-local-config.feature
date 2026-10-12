Feature: Pytester child projects use a local default feature root

  Scenario: Autoload uses the child project root when its features directory is absent
    Given a pytester child has a plain Python test that checks its local feature root
    When I run the pytester child with arguments "--cuke-autoload --cuke-parser=python -q"
    Then the pytester child should have one passing test

  Scenario: An explicitly selected missing child feature root remains an error
    Given a pytester child has a plain Python test that checks its local feature root
    When I run the pytester child with arguments "--cuke-autoload --cuke-parser=python --cuke-features-dir=missing-features -q"
    Then the pytester child should report its selected missing feature root

  Scenario: A custom child config keeps the feature root local
    Given a pytester child has a plain Python test that checks its local feature root
    And the pytester child has a nonstandard config file without a feature-root setting
    When I run the pytester child with arguments "-c child-pytest.ini --cuke-autoload --cuke-parser=python -q"
    Then the pytester child should have one passing test
