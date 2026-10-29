Feature: Windows drive-root feature sources

  Scenario: A Windows file URI keeps its editor source identity
    Given a Windows drive-rooted feature URI "file:///C:/workspace/my%20features/checkout.feature"
    When the feature source is bound to a runtime
    Then its bound URI and editor identity preserve the drive root
