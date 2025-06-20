from subprocess import CalledProcessError

from pytest_bdd.util.npm_resource import check_npm, check_npm_package

try:
    is_npm_gherkin_installed = all(
        [
            check_npm(),
            any(
                [
                    check_npm_package("@cucumber/gherkin", global_install=True),
                    check_npm_package("@cucumber/gherkin"),
                ],
            ),
        ],
    )
except CalledProcessError:
    is_npm_gherkin_installed = False
