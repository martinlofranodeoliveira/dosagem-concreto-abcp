"""Testes para tabelas empíricas, constantes normativas e limites ABCP / NBR.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from dosagem_concreto_abcp.constants import (
    CURVAS_ABRAMS_ABCP,
    DIAMETROS_MAXIMOS_VALIDOS,
    FATOR_QUANTIL_NORMAL,
    LIMITES_CAA,
    MODULOS_FINURA_TABELADOS,
    REGRAS_CONDICAO_PREPARO,
    SLUMPS_TABELADOS,
    TABELA_AR_APRISIONADO_LITROS,
    TABELA_CONSUMO_AGUA_ABCP,
    TABELA_VOLUME_APARENTE_BRITA,
)


class TestConstantsAndTables(unittest.TestCase):
    def test_fator_quantil_normal_e_1_65(self):
        self.assertEqual(FATOR_QUANTIL_NORMAL, Fraction(33, 20))
        self.assertEqual(float(FATOR_QUANTIL_NORMAL), 1.65)

    def test_regras_condicao_preparo_desvios_padrao(self):
        self.assertEqual(REGRAS_CONDICAO_PREPARO["A"].desvio_padrao_mpa, Fraction(4, 1))
        self.assertEqual(REGRAS_CONDICAO_PREPARO["B"].desvio_padrao_mpa, Fraction(11, 2))
        self.assertEqual(REGRAS_CONDICAO_PREPARO["C"].desvio_padrao_mpa, Fraction(7, 1))

    def test_regras_condicao_preparo_limites_fck(self):
        self.assertIsNone(REGRAS_CONDICAO_PREPARO["A"].fck_max_mpa)
        self.assertEqual(REGRAS_CONDICAO_PREPARO["B"].fck_max_mpa, Fraction(25, 1))
        self.assertEqual(REGRAS_CONDICAO_PREPARO["C"].fck_max_mpa, Fraction(15, 1))

    def test_limites_caa_relacoes_ac_maximas(self):
        self.assertEqual(LIMITES_CAA["CAA_I"].ac_maximo_ca, Fraction(13, 20))
        self.assertEqual(LIMITES_CAA["CAA_II"].ac_maximo_ca, Fraction(3, 5))
        self.assertEqual(LIMITES_CAA["CAA_III"].ac_maximo_ca, Fraction(11, 20))
        self.assertEqual(LIMITES_CAA["CAA_IV"].ac_maximo_ca, Fraction(9, 20))

    def test_limites_caa_fck_minimos(self):
        self.assertEqual(LIMITES_CAA["CAA_I"].fck_minimo_ca, Fraction(20, 1))
        self.assertEqual(LIMITES_CAA["CAA_II"].fck_minimo_ca, Fraction(25, 1))
        self.assertEqual(LIMITES_CAA["CAA_III"].fck_minimo_ca, Fraction(30, 1))
        self.assertEqual(LIMITES_CAA["CAA_IV"].fck_minimo_ca, Fraction(40, 1))

    def test_limites_caa_consumo_minimo_cimento(self):
        self.assertEqual(LIMITES_CAA["CAA_I"].consumo_cimento_minimo_kg_m3, Fraction(260, 1))
        self.assertEqual(LIMITES_CAA["CAA_II"].consumo_cimento_minimo_kg_m3, Fraction(280, 1))
        self.assertEqual(LIMITES_CAA["CAA_III"].consumo_cimento_minimo_kg_m3, Fraction(320, 1))
        self.assertEqual(LIMITES_CAA["CAA_IV"].consumo_cimento_minimo_kg_m3, Fraction(360, 1))

    def test_diametros_maximos_ordenados(self):
        self.assertEqual(
            DIAMETROS_MAXIMOS_VALIDOS,
            (Fraction(19, 2), Fraction(25, 2), Fraction(19, 1), Fraction(25, 1), Fraction(63, 2), Fraction(38, 1)),
        )

    def test_slumps_tabelados_ordenados(self):
        self.assertEqual(SLUMPS_TABELADOS, (40, 70, 100, 135, 170))

    def test_tabela_ar_aprisionado_decrescente_com_tamanho_grao(self):
        ar_9_5 = TABELA_AR_APRISIONADO_LITROS[Fraction(19, 2)]
        ar_19 = TABELA_AR_APRISIONADO_LITROS[Fraction(19, 1)]
        ar_38 = TABELA_AR_APRISIONADO_LITROS[Fraction(38, 1)]
        self.assertTrue(ar_9_5 > ar_19 > ar_38)
        self.assertEqual(ar_9_5, Fraction(30, 1))
        self.assertEqual(ar_19, Fraction(20, 1))
        self.assertEqual(ar_38, Fraction(8, 1))

    def test_curvas_abrams_monotonia_decrescente_de_fcm(self):
        for nome_curva, pontos in CURVAS_ABRAMS_ABCP.items():
            for i in range(len(pontos) - 1):
                ac_atual, fcm_atual = pontos[i]
                ac_prox, fcm_prox = pontos[i + 1]
                self.assertLess(ac_atual, ac_prox, f"Em {nome_curva}, a/c deve ser estritamente crescente.")
                self.assertGreater(fcm_atual, fcm_prox, f"Em {nome_curva}, fcm deve decrescer com a/c.")

    def test_tabela_volume_aparente_brita_cobre_todos_diametros_e_mf(self):
        for d in DIAMETROS_MAXIMOS_VALIDOS:
            self.assertIn(d, TABELA_VOLUME_APARENTE_BRITA)
            for mf in MODULOS_FINURA_TABELADOS:
                self.assertIn(mf, TABELA_VOLUME_APARENTE_BRITA[d])
                v = TABELA_VOLUME_APARENTE_BRITA[d][mf]
                self.assertGreater(v, Fraction(3, 10))
                self.assertLess(v, Fraction(9, 10))


if __name__ == "__main__":
    unittest.main()
