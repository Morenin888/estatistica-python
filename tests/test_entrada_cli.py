"""Valida leitura, localização dos erros e execução real dos pontos de entrada."""

from collections import Counter
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from estatistica.entrada import ErroEntrada, ler_csv, ler_dados_manuais


RAIZ = Path(__file__).resolve().parents[1]


class TestEntradaManual(unittest.TestCase):
    def test_inteiros_decimais_negativos_e_notacao_cientifica(self):
        self.assertEqual(ler_dados_manuais(" -2, 0, 1.5, 2e2 "), [-2.0, 0.0, 1.5, 200.0])

    def test_ponto_e_virgula_permite_decimal_com_virgula(self):
        self.assertEqual(ler_dados_manuais("1,5; -2,25; 3.5"), [1.5, -2.25, 3.5])

    def test_vazios_invalidos_e_nao_finitos(self):
        for texto in ("", "  ", "1,,2", "1,", "1;", "abc", "NaN", "inf", "-Infinity", "1e999"):
            with self.subTest(texto=texto), self.assertRaises(ErroEntrada):
                ler_dados_manuais(texto)

    def test_erro_identifica_posicao(self):
        with self.assertRaisesRegex(ErroEntrada, "Valor 2"):
            ler_dados_manuais("1,abc,3")


class TestEntradaCSV(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "dados.csv"

    def gravar(self, texto):
        self.caminho.write_text(texto, encoding="utf-8")
        return self.caminho

    def test_varias_colunas_numericas(self):
        self.assertEqual(ler_csv(self.gravar("1,2\n3,4\n")), [1, 2, 3, 4])

    def test_ponto_virgula_sem_cabecalho_com_decimais(self):
        self.assertEqual(ler_csv(self.gravar("1,5;2,5\n3,5;4,5\n")), [1.5, 2.5, 3.5, 4.5])

    def test_tab_com_decimais(self):
        self.assertEqual(ler_csv(self.gravar("1,5\t2,5\n3,5\t4,5\n")), [1.5, 2.5, 3.5, 4.5])

    def test_coluna_por_nome_e_bom_utf8(self):
        caminho = self.gravar("\ufeffnome;medida\nA;1,5\nB;2,5\n")
        self.assertEqual(ler_csv(caminho, coluna="medida", cabecalho=True), [1.5, 2.5])

    def test_coluna_por_indice_sem_cabecalho(self):
        self.assertEqual(ler_csv(self.gravar("A,1\nB,2\n"), coluna=2), [1, 2])

    def test_cabecalho_deve_ser_explicito(self):
        caminho = self.gravar("valor\n1\n2\n")
        with self.assertRaisesRegex(ErroEntrada, "Linha 1, coluna 1"):
            ler_csv(caminho)
        self.assertEqual(ler_csv(caminho, cabecalho=True), [1, 2])

    def test_linhas_vazias_nao_contam_como_cabecalho(self):
        self.assertEqual(ler_csv(self.gravar("\n  \nvalor\n\n1\n  \n2\n"), cabecalho=True), [1, 2])

    def test_celulas_entre_aspas(self):
        self.assertEqual(ler_csv(self.gravar('"1","2"\n"3","4"\n')), [1, 2, 3, 4])

    def test_campos_vazios_em_linhas_nao_vazias(self):
        for texto in ('""\n', "1,\n", ",2\n", "1; ;2\n"):
            with self.subTest(texto=texto), self.assertRaisesRegex(ErroEntrada, "campo vazio"):
                ler_csv(self.gravar(texto))

    def test_nao_finitos_e_strings_com_linha_coluna(self):
        for valor in ("abc", "nan", "inf", "1e999"):
            with self.subTest(valor=valor), self.assertRaisesRegex(ErroEntrada, "Linha 2, coluna 2"):
                ler_csv(self.gravar(f"1,2\n3,{valor}\n"))

    def test_csv_malformado(self):
        with self.assertRaisesRegex(ErroEntrada, "CSV inválido.*linha"):
            ler_csv(self.gravar('"1,2\n3,4\n'))

    def test_coluna_inexistente_e_indice_invalido(self):
        caminho = self.gravar("nome,valor\nA,1\n")
        for coluna in (0, -1, "0", "-1"):
            with self.subTest(coluna=coluna), self.assertRaisesRegex(ErroEntrada, "a partir de 1"):
                ler_csv(caminho, coluna=coluna, cabecalho=True)
        with self.assertRaisesRegex(ErroEntrada, "não encontrada"):
            ler_csv(caminho, coluna="ausente", cabecalho=True)
        with self.assertRaisesRegex(ErroEntrada, "coluna 3 não existe"):
            ler_csv(caminho, coluna=3, cabecalho=True)

    def test_coluna_nome_exige_cabecalho_e_nao_pode_ser_duplicada(self):
        caminho = self.gravar("valor,valor\n1,2\n")
        with self.assertRaisesRegex(ErroEntrada, "use --cabecalho"):
            ler_csv(caminho, coluna="valor")
        with self.assertRaisesRegex(ErroEntrada, "mais de uma vez"):
            ler_csv(caminho, coluna="valor", cabecalho=True)
        self.assertEqual(ler_csv(caminho, coluna=2, cabecalho=True), [2])

    def test_linha_sem_coluna_selecionada(self):
        with self.assertRaisesRegex(ErroEntrada, "Linha 2.*coluna 2 não existe"):
            ler_csv(self.gravar("1,2\n3\n"), coluna=2)

    def test_arquivo_vazio_so_cabecalho_e_inexistente(self):
        for texto in ("", " \n\n"):
            with self.subTest(texto=texto), self.assertRaisesRegex(ErroEntrada, "vazio"):
                ler_csv(self.gravar(texto))
        with self.assertRaisesRegex(ErroEntrada, "não contém dados"):
            ler_csv(self.gravar("valor\n"), cabecalho=True)
        with self.assertRaisesRegex(ErroEntrada, "não encontrado"):
            ler_csv(Path(self.temporario.name) / "ausente.csv")

    def test_permissao_e_codificacao_invalida(self):
        with patch("estatistica.entrada.Path.read_text", side_effect=PermissionError):
            with self.assertRaisesRegex(ErroEntrada, "Sem permissão"):
                ler_csv(self.caminho)
        self.caminho.write_bytes(b"\xff\xfe1,2")
        with self.assertRaisesRegex(ErroEntrada, "UTF-8"):
            ler_csv(self.caminho)

    def test_fixtures_de_exemplo(self):
        dados = ler_csv(RAIZ / "dados/exemplo.csv")
        self.assertEqual(Counter(dados), dict(enumerate([2, 4, 8, 12, 10, 6, 4, 2])))
        self.assertEqual(ler_csv(RAIZ / "dados/com_cabecalho.csv", coluna="valor", cabecalho=True), dados)
        self.assertEqual(
            ler_csv(RAIZ / "dados/decimais.csv", coluna="medida", cabecalho=True),
            [1.5, 2, 2.5, 3, 3.5, 4],
        )


class TestCLI(unittest.TestCase):
    def executar(self, *argumentos, entrada=None, modulo=False):
        comando = [sys.executable, "-m", "estatistica"] if modulo else [sys.executable, "main.py"]
        return subprocess.run(
            comando + list(argumentos), cwd=RAIZ, input=entrada, text=True,
            capture_output=True, timeout=10,
        )

    def test_analise_completa_dos_tres_niveis(self):
        resultado = self.executar("--csv", "dados/exemplo.csv")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        for texto in ("n = 48", "PARTE 1", "PARTE 2", "PARTE 3", "(xi)", "(fi)", "(Fi)", "k = 7", "Q1", "Q3", "D2", "D7", "P15", "P22", "P63", "P70", "Czuber"):
            with self.subTest(texto=texto):
                self.assertIn(texto, resultado.stdout)

    def test_execucao_modulo_e_decimais(self):
        resultado = self.executar("--dados", "1,5;2,5;3,5", modulo=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Média: 2.5", resultado.stdout)

    def test_csv_cabecalho_e_coluna(self):
        resultado = self.executar("--csv", "dados/com_cabecalho.csv", "--cabecalho", "--coluna", "valor")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("n = 48", resultado.stdout)

    def test_fontes_exclusivas_e_opcoes_sem_csv(self):
        for argumentos in (("--dados", "1,2", "--csv", "dados/exemplo.csv"), ("--cabecalho",), ("--dados", "1,2", "--coluna", "1")):
            with self.subTest(argumentos=argumentos):
                resultado = self.executar(*argumentos)
                self.assertEqual(resultado.returncode, 2)
                self.assertNotIn("Traceback", resultado.stderr)

    def test_erro_dados_sem_traceback(self):
        for argumentos in (("--dados", "1,nan"), ("--csv", "nao_existe.csv")):
            with self.subTest(argumentos=argumentos):
                resultado = self.executar(*argumentos)
                self.assertEqual(resultado.returncode, 1)
                self.assertIn("Erro:", resultado.stderr)
                self.assertNotIn("Traceback", resultado.stderr)

    def test_menu_repeticao_apos_erros(self):
        resultado = self.executar(entrada="9\n1\n1,abc\n1\n1,2,3\n0\n")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Opção inválida", resultado.stdout)
        self.assertIn("Valor 2", resultado.stdout)
        self.assertIn("PARTE 3", resultado.stdout)
        self.assertIn("Programa encerrado", resultado.stdout)

    def test_menu_csv_e_eof_limpo(self):
        resultado = self.executar(entrada="2\ndados/com_cabecalho.csv\ns\nvalor\n")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("n = 48", resultado.stdout)
        self.assertIn("Programa encerrado", resultado.stdout)
        self.assertNotIn("Traceback", resultado.stderr)

    def test_constantes_e_empate_moda(self):
        constante = self.executar("--dados", "5,5,5")
        self.assertEqual(constante.returncode, 0, constante.stderr)
        self.assertIn("Dados constantes", constante.stdout)
        self.assertIn("k = 3 (Sturges)", constante.stdout)
        self.assertIn("Classes efetivas = 1", constante.stdout)
        empate = self.executar("--dados", "2,1,2,1")
        self.assertEqual(empate.returncode, 0, empate.stderr)
        self.assertIn("primeira moda encontrada", empate.stdout)
        self.assertIn("Moda(s) = 1, 2", empate.stdout)

    def test_overflow_statistics_resultado_infinito_e_recusado(self):
        resultado = self.executar("--dados", "1e308,1e308")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("statistics produziu um resultado não finito", resultado.stderr)
        self.assertNotIn("Traceback", resultado.stderr)

    def test_ajuda_portugues(self):
        resultado = self.executar("--help")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("uso:", resultado.stdout)
        self.assertIn("Opções", resultado.stdout)
        self.assertIn("--cabecalho", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
