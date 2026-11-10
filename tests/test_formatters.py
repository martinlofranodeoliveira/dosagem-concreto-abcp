"""Testes para formatadores determinísticos em pt-BR.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from dosagem_concreto_abcp.domain import AjusteCanteiro, TracoMassa
from dosagem_concreto_abcp.formatters import (
    formatar_fracao_decimal,
    formatar_moeda,
    formatar_traco_saco_50kg,
    formatar_traco_unitario,
)


class TestFormatters(unittest.TestCase):
    def test_formatar_fracao_decimal_zero(self):
        self.assertEqual(formatar_fracao_decimal(Fraction(0, 1), casas=2), "0,00")
        self.assertEqual(formatar_fracao_decimal(0, casas=0), "0")

    def test_formatar_fracao_decimal_half_up(self):
        # 1/8 = 0.125 -> 2 casas deve ser 0,13
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 8), casas=2), "0,13")
        # 3/8 = 0.375 -> 2 casas deve ser 0,38
        self.assertEqual(formatar_fracao_decimal(Fraction(3, 8), casas=2), "0,38")
        # 1/4 = 0.25 -> 1 casa deve ser 0,3
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 4), casas=1), "0,3")

    def test_formatar_fracao_decimal_negativo(self):
        # -3/2 = -1.50
        self.assertEqual(formatar_fracao_decimal(Fraction(-3, 2), casas=2), "-1,50")

    def test_formatar_fracao_decimal_separador_milhar(self):
        val = Fraction(1234567, 100)  # 12345.67
        self.assertEqual(
            formatar_fracao_decimal(val, casas=2, separador_milhar=True),
            "12.345,67",
        )

    def test_formatar_moeda(self):
        val = Fraction(1550, 100)
        self.assertEqual(formatar_moeda(val), "R$ 15,50")

        val_milhar = Fraction(2750000, 100)
        self.assertEqual(formatar_moeda(val_milhar), "R$ 27.500,00")

    def test_formatar_traco_unitario_uma_brita(self):
        traco = TracoMassa(
            cimento=Fraction(1, 1),
            areia=Fraction(215, 100),
            britas=(("Brita 1", Fraction(285, 100)),),
            brita_total=Fraction(285, 100),
            agua_cimento=Fraction(52, 100),
            soma_agregados_m=Fraction(5, 1),
            teor_argamassa_pct=Fraction(525, 10),
        )
        self.assertEqual(formatar_traco_unitario(traco), "1 : 2,15 : 2,85 : 0,52")

    def test_formatar_traco_unitario_multiplas_britas(self):
        traco = TracoMassa(
            cimento=Fraction(1, 1),
            areia=Fraction(200, 100),
            britas=(
                ("Brita 1", Fraction(180, 100)),
                ("Brita 2", Fraction(120, 100)),
            ),
            brita_total=Fraction(300, 100),
            agua_cimento=Fraction(50, 100),
            soma_agregados_m=Fraction(5, 1),
            teor_argamassa_pct=Fraction(50, 1),
        )
        self.assertEqual(
            formatar_traco_unitario(traco),
            "1 : 2,00 : 3,00 [1,80 (Brita 1) + 1,20 (Brita 2)] : 0,50",
        )

    def test_formatar_traco_saco_50kg(self):
        ajuste = AjusteCanteiro(
            areia_umida_kg_m3=Fraction(750, 1),
            britas_umidas_kg_m3=(("Brita 1", Fraction(1000, 1)),),
            agua_efetiva_litros_m3=Fraction(180, 1),
            agua_contida_agregados_litros_m3=Fraction(20, 1),
            traco_saco_50kg_cimento_kg=Fraction(50, 1),
            traco_saco_50kg_areia_umida_kg=Fraction(1125, 10),
            traco_saco_50kg_britas_umidas_kg=(("Brita 1", Fraction(150, 1)),),
            traco_saco_50kg_agua_litros=Fraction(27, 1),
            volume_areia_padiolas_litros=None,
            volumes_brita_padiolas_litros=None,
        )
        res = formatar_traco_saco_50kg(ajuste)
        self.assertIn("50,0 kg cimento", res)
        self.assertIn("112,5 kg areia úmida", res)
        self.assertIn("150,0 kg de brita", res)
        self.assertIn("27,0 L de água a adicionar", res)


if __name__ == "__main__":
    unittest.main()
