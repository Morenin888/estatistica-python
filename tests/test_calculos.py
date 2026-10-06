"""Oráculos manuais e casos de fronteira para o núcleo matemático."""

import math
import unittest

from estatistica import (
    Classe, DistribuicaoClasses, LinhaDiscreta, analisar_nao_agrupados,
    calcular_medidas_classes, calcular_medidas_discretas, calcular_separatriz,
    construir_distribuicao, construir_tabela_discreta, criar_distribuicao_manual,
    validar_dados,
)


class TestDadosNaoAgrupados(unittest.TestCase):
    def test_oraculo_tendencia_central(self):
        resultado = analisar_nao_agrupados(validar_dados([1, 2, 2, 3, 7]))
        self.assertEqual(resultado.media, 3)
        self.assertEqual(resultado.mediana, 2)
        self.assertEqual(resultado.moda, 2)

    def test_empate_preserva_primeira_moda_statistics(self):
        resultado = analisar_nao_agrupados(validar_dados([4, 1, 1, 4]))
        self.assertEqual(resultado.moda, 4)
        self.assertEqual(resultado.mediana, 2.5)

    def test_amostra_unitaria(self):
        resultado = analisar_nao_agrupados(validar_dados([-3.25]))
        self.assertEqual((resultado.media, resultado.mediana, resultado.moda),
                         (-3.25, -3.25, -3.25))


class TestDistribuicaoDiscreta(unittest.TestCase):
    def test_tabela_e_oraculo_decimal_negativo(self):
        tabela = construir_tabela_discreta([-2.5, -2.5, -1, .5, .5, .5])
        self.assertEqual(tabela, [LinhaDiscreta(-2.5, 2, 2),
                                 LinhaDiscreta(-1, 1, 3), LinhaDiscreta(.5, 3, 6)])
        resultado = calcular_medidas_discretas(tabela)
        self.assertAlmostEqual(resultado.media, -.75)
        self.assertEqual(resultado.mediana, -.25)
        self.assertEqual(resultado.modas, [.5])

    def test_mediana_impar_consulta_frequencia_acumulada(self):
        tabela = [LinhaDiscreta(1, 2, 2), LinhaDiscreta(10, 3, 5),
                  LinhaDiscreta(100, 2, 7)]
        resultado = calcular_medidas_discretas(tabela)
        self.assertEqual(resultado.mediana, 10)
        self.assertAlmostEqual(resultado.media, 232 / 7)
        self.assertEqual(resultado.modas, [10])

    def test_modas_empatadas(self):
        resultado = calcular_medidas_discretas(construir_tabela_discreta([5, 1, 5, 1]))
        self.assertEqual(resultado.modas, [1, 5])
        self.assertIn("empate", resultado.observacao_moda)

    def test_sem_moda_predominante(self):
        resultado = calcular_medidas_discretas(construir_tabela_discreta([4, 1, 2]))
        self.assertEqual(resultado.modas, [1, 2, 4])
        self.assertIn("não há moda predominante", resultado.observacao_moda)

    def test_media_e_mediana_evitam_overflow_intermediario(self):
        tabela = [LinhaDiscreta(1e308, 10, 10), LinhaDiscreta(1.5e308, 10, 20)]
        resultado = calcular_medidas_discretas(tabela)
        self.assertAlmostEqual(resultado.media / 1e308, 1.25)
        self.assertAlmostEqual(resultado.mediana / 1e308, 1.25)

    def test_mediana_constante_subnormal_nao_desaparece(self):
        resultado = calcular_medidas_discretas(construir_tabela_discreta([5e-324, 5e-324]))
        self.assertEqual(resultado.media, 5e-324)
        self.assertEqual(resultado.mediana, 5e-324)

    def test_tabela_invalida(self):
        tabelas = [[], [LinhaDiscreta(1, 2, 1)], [LinhaDiscreta(1, 0, 0)],
                   [LinhaDiscreta(2, 1, 1), LinhaDiscreta(1, 1, 2)],
                   [LinhaDiscreta(1, 1, 1), LinhaDiscreta(1, 1, 2)],
                   [LinhaDiscreta(float("nan"), 1, 1)]]
        for tabela in tabelas:
            with self.subTest(tabela=tabela), self.assertRaises(ValueError):
                calcular_medidas_discretas(tabela)


class TestClasses(unittest.TestCase):
    def test_oraculo_tabela_classica_sem_copiar_resultados_ilustrativos_pdf(self):
        # Somatório ponderado = 2 984, n = 120. Classe mediana/moda: [22,26).
        distribuicao = criar_distribuicao_manual([18, 22, 26, 30, 34], [32, 45, 28, 15])
        resultado = calcular_medidas_classes(distribuicao)
        self.assertAlmostEqual(resultado.media, 2984 / 120)
        self.assertAlmostEqual(resultado.mediana, 22 + (60 - 32) * 4 / 45)
        self.assertAlmostEqual(resultado.modas[0], 22 + 13 * 4 / 30)
        esperados = {"Q1": 21.75, "Q3": 27.857142857142858,
                     "D2": 21, "D7": 27, "P15": 20.25, "P22": 21.3,
                     "P63": 25.875555555555554, "P70": 27}
        obtidos = {**resultado.quartis, **resultado.decis, **resultado.percentis}
        for nome, esperado in esperados.items():
            with self.subTest(separatriz=nome):
                self.assertAlmostEqual(obtidos[nome], esperado)

    def test_sturges_limites_exatos_e_maximo_incluido(self):
        dados = [0, 2, 4, 6, 8, 10, 1, 3, 5, 7]
        distribuicao = construir_distribuicao(dados)
        self.assertEqual(distribuicao.quantidade_classes, 5)
        self.assertEqual(distribuicao.amplitude_classe, 2)
        self.assertEqual([c.limite_inferior for c in distribuicao.classes], [0, 2, 4, 6, 8])
        self.assertEqual([c.frequencia for c in distribuicao.classes], [2, 2, 2, 2, 2])
        self.assertEqual(distribuicao.classes[-1].acumulada, 10)

    def test_observacao_logo_abaixo_de_fronteira_nao_e_arredondada(self):
        abaixo_de_dois = math.nextafter(2.0, -math.inf)
        dados = [0, abaixo_de_dois, 2, 4, 6, 8, 10, 1, 3, 5]
        distribuicao = construir_distribuicao(dados)
        self.assertEqual([c.frequencia for c in distribuicao.classes], [3, 2, 2, 1, 2])

    def test_decimais_preservam_todas_observacoes(self):
        distribuicao = construir_distribuicao([i / 10 for i in range(10)])
        self.assertEqual([c.frequencia for c in distribuicao.classes], [2, 2, 2, 2, 2])
        self.assertEqual(sum(c.frequencia for c in distribuicao.classes), 10)

    def test_constantes_incluindo_amostra_unitaria(self):
        for dados in ([-2.75], [-2.75] * 12, [0] * 4):
            with self.subTest(n=len(dados)):
                distribuicao = construir_distribuicao(dados)
                resultado = calcular_medidas_classes(distribuicao)
                self.assertEqual(distribuicao.quantidade_classes, 1)
                self.assertEqual(distribuicao.amplitude_classe, 0)
                self.assertEqual(resultado.media, dados[0])
                self.assertEqual(resultado.mediana, dados[0])
                self.assertEqual(resultado.modas, [dados[0]])
                for valor in (*resultado.quartis.values(), *resultado.decis.values(),
                              *resultado.percentis.values()):
                    self.assertEqual(valor, dados[0])

    def test_duas_observacoes_sturges_pode_gerar_classe_vazia(self):
        distribuicao = construir_distribuicao([0, 10])
        # 3.322 * log10(2) é ligeiramente maior que 1: o ceil produz k = 3.
        self.assertEqual(distribuicao.quantidade_classes, 3)
        self.assertEqual([c.frequencia for c in distribuicao.classes], [1, 0, 1])
        resultado = calcular_medidas_classes(distribuicao)
        self.assertAlmostEqual(resultado.media, 5)
        self.assertAlmostEqual(resultado.mediana, 10 / 3)
        self.assertEqual(resultado.modas, [])
        self.assertIn("Frequência máxima igual a 1", resultado.observacao_moda)

    def test_classes_negativas_e_separatriz_exatamente_na_fronteira(self):
        resultado = calcular_medidas_classes(criar_distribuicao_manual([-2, 0, 2, 4], [2, 4, 2]))
        self.assertAlmostEqual(resultado.media, 1)
        self.assertEqual(resultado.mediana, 1)
        self.assertEqual(resultado.modas, [1])
        self.assertEqual(resultado.quartis, {"Q1": 0, "Q3": 2})

    def test_classes_vazias_nao_causam_divisao_por_zero(self):
        distribuicao = criar_distribuicao_manual([0, 10, 20, 30], [4, 0, 4])
        resultado = calcular_medidas_classes(distribuicao)
        self.assertEqual(resultado.media, 15)
        self.assertEqual(resultado.mediana, 10)
        self.assertEqual(resultado.quartis["Q3"], 25)
        self.assertEqual(resultado.modas, [5, 25])
        self.assertIn("empate", resultado.observacao_moda)

    def test_czuber_classe_modal_nas_bordas(self):
        for frequencias, esperado in (([6, 2, 1], .6), ([1, 2, 6], 2.4)):
            with self.subTest(frequencias=frequencias):
                resultado = calcular_medidas_classes(criar_distribuicao_manual([0, 1, 2, 3], frequencias))
                self.assertAlmostEqual(resultado.modas[0], esperado)

    def test_czuber_empate_contiguo_e_plateau(self):
        distribuicao = criar_distribuicao_manual([0, 1, 2, 3, 4, 5], [1, 4, 4, 4, 1])
        resultado = calcular_medidas_classes(distribuicao)
        self.assertEqual(resultado.classes_modais, [1, 2, 3])
        self.assertEqual(resultado.modas, [2, 3])
        self.assertIn("não determinam uma moda única", resultado.observacao_moda)
        self.assertIn("d1 + d2 = 0", resultado.observacao_moda)

    def test_classes_equiprovaveis_sem_moda_unica(self):
        resultado = calcular_medidas_classes(criar_distribuicao_manual([0, 1, 2, 3], [2, 2, 2]))
        self.assertEqual(resultado.modas, [])
        self.assertIn("moda não é única", resultado.observacao_moda)

    def test_dataclasses_diretas_permitidas(self):
        distribuicao = DistribuicaoClasses([Classe(0, 1, 2, 2), Classe(1, 2, 6, 8)],
                                          8, 2, 2, 1)
        resultado = calcular_medidas_classes(distribuicao)
        self.assertEqual(resultado.media, 1.25)
        self.assertAlmostEqual(resultado.mediana, 4 / 3)
        self.assertAlmostEqual(resultado.modas[0], 1.4)

    def test_distribuicao_com_acumulada_inconsistente_rejeitada(self):
        distribuicao = DistribuicaoClasses([Classe(0, 1, 2, 1)], 2, 1, 1, 1)
        with self.assertRaises(ValueError):
            calcular_medidas_classes(distribuicao)

    def test_tabelas_manuais_invalidas(self):
        entradas = [([], []), ([0, 1], [0]), ([0, 1], [-1]),
                    ([0, 1], [1.5]), ([0, 0, 1], [1, 1]),
                    ([0, 1, 3], [1, 1]), ([1, 0], [1]),
                    ([0, math.inf], [1]), ([0, 1, 2], [1])]
        for limites, frequencias in entradas:
            with self.subTest(limites=limites, frequencias=frequencias), self.assertRaises(ValueError):
                criar_distribuicao_manual(limites, frequencias)

    def test_overflow_e_limites_degenerados_rejeitados(self):
        for dados in ([-1e308, 1e308], [1e16, 1e16 + 2], [0.0, 5e-324]):
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                construir_distribuicao(dados)

    def test_total_manual_fora_intervalo_float_rejeitado(self):
        with self.assertRaises(ValueError):
            criar_distribuicao_manual([0, 1], [10 ** 1000])

    def test_separatriz_rejeita_proporcao_invalida(self):
        distribuicao = criar_distribuicao_manual([0, 1], [2])
        for proporcao in (-.1, 1.1, math.nan):
            with self.subTest(proporcao=proporcao), self.assertRaises(ValueError):
                calcular_separatriz(distribuicao, proporcao)


class TestValidacao(unittest.TestCase):
    def test_dados_invalidos(self):
        for dados in ([], None, [math.nan], [math.inf], [-math.inf], ["1"], [True], [10 ** 1000]):
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                validar_dados(dados)

    def test_entrada_nao_e_mutada(self):
        dados = [3, 1, 2]
        construir_tabela_discreta(dados)
        construir_distribuicao(dados)
        self.assertEqual(dados, [3, 1, 2])


if __name__ == "__main__":
    unittest.main()
