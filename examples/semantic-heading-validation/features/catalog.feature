Feature: Semantic heading validation example

  Scenario: A titled scenario runs after collection
    Given the catalog contains a book
    When the reader searches for that book
    Then the search returns the catalog book
