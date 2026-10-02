Features
========

.. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
          use cases of **pytest-cuke** by investigation of its regression
          test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/rewrite-from-2.3.1/tests



pytest-cuke-bootstrap
---------------------

.. include:: ../features/pytest-cuke-bootstrap.feature
   :code: gherkin

tutorial
--------

launch
######

.. include:: features/tutorial/launch.feature.rst

step-definition
---------------

pytest-fixtures-substitution
############################

.. include:: features/step-definition/pytest-fixtures-substitution.feature.rst

target-fixtures-specification
#############################

.. include:: features/step-definition/target-fixtures-specification.feature.rst

parameters
##########

conversion
!!!!!!!!!!

.. include:: features/step-definition/parameters/conversion.feature.rst

defaults
!!!!!!!!

.. include:: features/step-definition/parameters/defaults.feature.rst

injection-as-fixtures
!!!!!!!!!!!!!!!!!!!!!

.. include:: features/step-definition/parameters/injection-as-fixtures.feature.rst

parsing-by-custom-parser
!!!!!!!!!!!!!!!!!!!!!!!!

.. include:: features/step-definition/parameters/parsing-by-custom-parser.feature.rst

parsing
!!!!!!!

.. include:: features/step-definition/parameters/parsing.feature.rst

step
----

data-table
##########

.. include:: features/step/data-table.feature.rst

doc-string
##########

.. include:: features/step/doc-string.feature.rst

step-definition-bounding
########################

.. include:: features/step/step-definition-bounding.feature.rst

scenario
--------

description
###########

.. include:: features/scenario/description.feature.rst

tag
###

.. include:: features/scenario/tag.feature.rst

outline
#######

examples-tag
!!!!!!!!!!!!

.. include:: features/scenario/outline/examples-tag.feature.rst

report
------

gathering
#########

.. include:: features/report/gathering.feature.rst

feature
-------

description
###########

.. include:: features/feature/description.feature.rst

localization
############

.. include:: features/feature/localization.feature.rst

tag-conversion
##############

.. include:: features/feature/tag-conversion.feature.rst

tag
###

.. include:: features/feature/tag.feature.rst

load
####

autoload
!!!!!!!!

.. include:: features/feature/load/autoload.feature.rst

scenario-function-loader
!!!!!!!!!!!!!!!!!!!!!!!!

.. include:: features/feature/load/scenario-function-loader.feature.rst

scenario-search-from-base-directory
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. include:: features/feature/load/scenario-search-from-base-directory.feature.rst

scenario-search-from-base-url
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. include:: features/feature/load/scenario-search-from-base-url.feature.rst
