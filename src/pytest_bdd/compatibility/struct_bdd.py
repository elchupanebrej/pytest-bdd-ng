import importlib.util

STRUCT_BDD_INSTALLED = importlib.util.find_spec("pytest_bdd.struct_bdd.parser.StructBDDParser") is not None
