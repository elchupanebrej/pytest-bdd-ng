Feature: Tag expression evaluation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Verify parsing and evaluation of tag expressions against markers.

Scenario: Evaluate AND expression
'''''''''''''''''''''''''''''''''

- Given Tag expression "smoke and login"
- Then Tag expression evaluates to True for marks "['smoke', 'login']"
- And Tag expression evaluates to False for marks "['smoke', 'slow']"

Scenario: Evaluate OR expression
''''''''''''''''''''''''''''''''

- Given Tag expression "smoke or slow"
- Then Tag expression evaluates to True for marks "['smoke', 'login']"
- And Tag expression evaluates to True for marks "['slow', 'login']"
- And Tag expression evaluates to False for marks "['login',
  'regression']"

Scenario: Evaluate NOT expression
'''''''''''''''''''''''''''''''''

- Given Tag expression "smoke and not slow"
- Then Tag expression evaluates to True for marks "['smoke', 'login']"
- And Tag expression evaluates to False for marks "['smoke', 'slow']"

Scenario: Complex boolean expression
''''''''''''''''''''''''''''''''''''

- Given Complex boolean tag expression "(smoke or regression) and not
  slow"
- Then Tag expression evaluates to True for marks "['smoke', 'login']"
- And Tag expression evaluates to True for marks "['regression']"
- And Tag expression evaluates to False for marks "['smoke', 'slow']"
