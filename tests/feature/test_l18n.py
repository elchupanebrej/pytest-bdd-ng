def test_pt_l18n(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            #language: pt
            #encoding: UTF-8
            Funcionalidade: Login no Programa
                Cenário: O usuário ainda não é cadastrado
                    Dado que o usuário esteja na tela de login
                    Quando ele clicar no botão de Criar Conta
                    Então ele deve ser levado para a tela de criação de conta
            """,
    )
    testdir.makepyfile(
        """\
            import pytest

            from pytest_bdd import scenarios, given, when, then, parsers

            test_cukes = scenarios("steps.feature")

            @given("que o usuário esteja na tela de login")
            def tela_login():
                assert True

            @when("ele clicar no botão de Criar Conta")
            def evento_criar_conta():
                assert True

            @then("ele deve ser levado para a tela de criação de conta")
            def tela_criacao_conta():
                assert True
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)
