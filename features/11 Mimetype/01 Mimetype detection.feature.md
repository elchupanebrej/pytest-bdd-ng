# Feature: Mimetype detection
  Verify correct mimetype resolution for files.

## Scenario: Detect .feature extension as gherkin_plain
* Given File extension is .feature
* Then Mimetype resolves to text/x.cucumber.gherkin+plain

## Scenario: Detect .feature.md extension as gherkin_markdown
* Given File extension is .feature.md
* Then Mimetype resolves to text/x.cucumber.gherkin+markdown

## Scenario: Detect .bdd.yaml extension as struct_bdd_yaml
* Given File extension is .bdd.yaml
* Then Mimetype resolves to application/x.struct_bdd+yaml

## Scenario: Mimetype hook override routes correctly
* Given Mimetype hook override is set
* Then custom mimetype is used
