Feature: Mimetype detection edge cases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Verify mimetype resolution for struct_bdd formats and additional suffix
combinations.

Scenario: StructBDD hjson extension resolves correctly
''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File extension is .bdd.hjson
- Then Mimetype resolves to application/x.struct_bdd+hjson

Scenario: StructBDD json5 extension resolves correctly
''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File extension is .bdd.json5
- Then Mimetype resolves to application/x.struct_bdd+json5

Scenario: StructBDD toml extension resolves correctly
'''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File extension is .bdd.toml
- Then Mimetype resolves to application/x.struct_bdd+toml

Scenario: StructBDD hocon extension resolves correctly
''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File extension is .bdd.hocon
- Then Mimetype resolves to application/x.struct_bdd+hocon
