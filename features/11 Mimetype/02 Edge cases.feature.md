# Feature: Mimetype detection edge cases
  Verify mimetype resolution for struct_bdd formats and additional suffix combinations.

## Scenario Outline: StructBDD extension resolves correctly
* Given File extension is <extension>
* Then Mimetype resolves to <mimetype>

### Examples:

| extension  | mimetype                       |
|------------|--------------------------------|
| .bdd.hjson | application/x.struct_bdd+hjson |
| .bdd.json5 | application/x.struct_bdd+json5 |
| .bdd.toml  | application/x.struct_bdd+toml  |
| .bdd.hocon | application/x.struct_bdd+hocon |
