"""Testes para os exportadores Markdown, CSV e SVG vetorial.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from dosagem_concreto_abcp.calculator import calcular_dosagem_abcp
from dosagem_concreto_abcp.domain import (
    AgregadoGraudo,
    AgregadoMiudo,
    Cimento,
    ClasseAgressividadeAmbiental,
    CondicaoPreparo,
    ParametrosDosagem,
    PrecosUnitarios,
    TipoCimento,
    TipoEstrutura,
)
from dosagem_concreto_abcp.exports import (
    gerar_csv,
    gerar_markdown,
    gerar_painel_svg,
    sanitizar_campo_csv,
)


class TestExports(unittest.TestCase):
    def setUp(self):
        self.params = ParametrosDosagem(
            identificacao="Caso Exportacao Teste",
            fck_mpa=Fraction(25, 1),
            condicao_preparo=CondicaoPreparo.A,
            classe_agressividade=ClasseAgressividadeAmbiental.CAA_II,
            tipo_estrutura=TipoEstrutura.CONCRETO_ARMADO,
            slump_mm=80,
            cimento=Cimento(tipo=TipoCimento.CP_II_32),
            areia=AgregadoMiudo(
                nome="Areia Média",
                modulo_finura=Fraction(24, 10),
                massa_especifica_real_kg_l=Fraction(265, 100),
                umidade_pct=Fraction(3, 1),
            ),
            britas=(
                AgregadoGraudo(
                    nome="Brita 1",
                    d_max_mm=Fraction(19, 1),
                    massa_unitaria_compactada_kg_m3=Fraction(1500, 1),
                    massa_especifica_real_kg_l=Fraction(268, 100),
                    umidade_pct=Fraction(1, 2),
                ),
            ),
            precos=PrecosUnitarios(
                cimento_por_saco_50kg=Fraction(3850, 100),
                areia_por_metro_cubico=Fraction(120, 1),
                brita_por_metro_cubico=Fraction(110, 1),
                agua_por_metro_cubico=Fraction(85, 10),
            ),
        )
        self.resultado = calcular_dosagem_abcp(self.params)

    def test_sanitizar_campo_csv_formula_injection(self):
        self.assertEqual(sanitizar_campo_csv("=1+1"), "'=1+1")
        self.assertEqual(sanitizar_campo_csv("+2*3"), "'+2*3")
        self.assertEqual(sanitizar_campo_csv("-5+2"), "'-5+2")
        self.assertEqual(sanitizar_campo_csv("@SUM(A1:A5)"), "'@SUM(A1:A5)")
        self.assertEqual(sanitizar_campo_csv("\tcmd"), "'\tcmd")
        self.assertEqual(sanitizar_campo_csv("\rcmd"), "'\rcmd")
        self.assertEqual(sanitizar_campo_csv("Normal"), "Normal")

    def test_gerar_markdown_contem_secoes_principais(self):
        md = gerar_markdown(self.resultado)
        self.assertIn("# Memorial de Cálculo de Dosagem de Concreto", md)
        self.assertIn("ABNT NBR 12655:2022", md)
        self.assertIn("1. Parâmetros de Entrada", md)
        self.assertIn("2. Resistência de Dosagem", md)
        self.assertIn("3. Consumos de Materiais", md)
        self.assertIn("4. Traço Unitário em Massa Seca", md)
        self.assertIn("5. Ajuste Operacional para Canteiro", md)
        self.assertIn("6. Estimativa de Custos", md)
        self.assertIn("7. Quadro de Conformidade Normativa", md)

    def test_gerar_csv_delimitador_e_conteudo(self):
        csv = gerar_csv(self.resultado)
        linhas = csv.strip().split("\n")
        self.assertGreater(len(linhas), 20)
        self.assertIn(";", linhas[0])
        self.assertIn("RELATORIO DE DOSAGEM DE CONCRETO", linhas[0])
        self.assertIn("Cimento", csv)
        self.assertIn("Areia Seca", csv)
        self.assertIn("Brita", csv)

    def test_gerar_painel_svg_estrutura_e_dimensoes(self):
        svg = gerar_painel_svg(self.resultado)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.strip().endswith("</svg>"))
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn("DOSAGEM DE CONCRETO", svg)
        self.assertIn("TRAÇO UNITÁRIO EM MASSA SECA", svg)
        self.assertIn("LOFRANO TECNOLOGIA", svg)


if __name__ == "__main__":
    unittest.main()
