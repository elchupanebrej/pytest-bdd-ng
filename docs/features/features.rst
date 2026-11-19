Features
========

.. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
          use cases of **pytest-cuke** by investigation of its regression
          test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/rewrite-from-2.3.1/tests



mypy-runtime-gate
-----------------

.. include:: ../../features/mypy-runtime-gate.feature
   :code: gherkin

pytest-cuke-bootstrap
---------------------

.. include:: ../../features/pytest-cuke-bootstrap.feature
   :code: gherkin

feature-source-selection
------------------------

.. include:: ../../features/feature-source-selection.feature
   :code: gherkin

tutorial
--------

launch
######

.. include:: tutorial/launch.feature.rst

step-definition
---------------

tolerant-step-status
####################

.. include:: step-definition/tolerant-step-status.rst

pytest-fixtures-substitution
############################

.. include:: step-definition/pytest-fixtures-substitution.feature.rst

target-fixtures-specification
#############################

.. include:: step-definition/target-fixtures-specification.feature.rst

parameters
##########

conversion
^^^^^^^^^^

.. include:: step-definition/parameters/conversion.feature.rst

defaults
^^^^^^^^

.. include:: step-definition/parameters/defaults.feature.rst

injection-as-fixtures
^^^^^^^^^^^^^^^^^^^^^

.. include:: step-definition/parameters/injection-as-fixtures.feature.rst

parsing-by-custom-parser
^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: step-definition/parameters/parsing-by-custom-parser.feature.rst

parsing
^^^^^^^

.. include:: step-definition/parameters/parsing.feature.rst

step
----

data-table
##########

.. include:: step/data-table.feature.rst

doc-string
##########

.. include:: step/doc-string.feature.rst

step-definition-bounding
########################

.. include:: step/step-definition-bounding.feature.rst

scenario
--------

description
###########

.. include:: scenario/description.feature.rst

tag
###

.. include:: scenario/tag.feature.rst

outline
#######

examples-tag
^^^^^^^^^^^^

.. include:: scenario/outline/examples-tag.feature.rst

report
------

gathering
#########

.. include:: report/gathering.feature.rst

heading-validation
------------------

semantic-heading-validation
###########################

.. include:: ../../features/heading-validation/semantic-heading-validation.feature
   :code: gherkin

feature
-------

description
###########

.. include:: feature/description.feature.rst

localization
############

.. include:: feature/localization.feature.rst

tag-conversion
##############

.. include:: feature/tag-conversion.feature.rst

tag
###

.. include:: feature/tag.feature.rst

load
####

custom-parser-adapter
^^^^^^^^^^^^^^^^^^^^^^

.. include:: feature/load/custom-parser-adapter.rst

autoload
^^^^^^^^

.. include:: feature/load/autoload.feature.rst

external-examples
^^^^^^^^^^^^^^^^^

.. include:: feature/load/external-examples.feature.rst

scenario-function-loader
^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: feature/load/scenario-function-loader.feature.rst

scenario-search-from-base-directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: feature/load/scenario-search-from-base-directory.feature.rst

scenario-search-from-base-url
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: feature/load/scenario-search-from-base-url.feature.rst
