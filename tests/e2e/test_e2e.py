from pytest_bdd import scenarios

from pytest import mark

pytestmark = mark.e2e


test = scenarios("features")
