"""Testes para o motor de cálculo da dosagem ABCP.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from dosagem_concreto_abcp.calculator import (
    calcular_ajuste_canteiro,
    calcular_consumo_agua,
    calcular_custos,
    calcular_dosagem_abcp,
    calcular_fcm,
    calcular_relacao_ac_resistencia,
    calcular_volume_aparente_brita,
    interpolar_linear_racional,
    obter_desvio_padrao,
    obter_limites_caa,
)
from dosagem_concreto_abcp.domain import (
    AgregadoGraudo,
    AgregadoMiudo,
    Cimento,
    ClasseAgressividadeAmbiental,
    CondicaoPreparo,
    ConsumosMetroCubico,
    ParametrosDosagem,
    PrecosUnitarios,
    TipoCimento,
    TipoEstrutura,
)
from dosagem_concreto_abcp.errors import (
    ErroCondicaoPreparoIncompativel,
    ErroConsumoCimentoInvalido,
    ErroResistenciaInvalida,
    ErroSlumpInvalido,
)


class TestCalculator(unittest.TestCase):
    def test_obter_desvio_padrao(self):
        self.assertEqual(obter_desvio_padrao(CondicaoPreparo.A), Fraction(4, 1))
        self.assertEqual(obter_desvio_padrao(CondicaoPreparo.B), Fraction(11, 2))
        self.assertEqual(obter_desvio_padrao(CondicaoPreparo.C), Fraction(7, 1))

    def test_calcular_fcm_condicao_a(self):
        # fcm = 25 + 1.65 * 4 = 25 + 6.6 = 31.6
        fck = Fraction(25, 1)
        fcm = calcular_fcm(fck, CondicaoPreparo.A)
        self.assertEqual(fcm, Fraction(158, 5))
        self.assertEqual(float(fcm), 31.6)

    def test_calcular_fcm_condicao_b(self):
        # fcm = 20 + 1.65 * 5.5 = 20 + 9.075 = 29.075
        fck = Fraction(20, 1)
        fcm = calcular_fcm(fck, CondicaoPreparo.B)
        self.assertEqual(fcm, Fraction(1163, 40))
        self.assertEqual(float(fcm), 29.075)

    def test_interpolar_linear_racional_caso_comum(self):
        res = interpolar_linear_racional(
            Fraction(5, 1),
            Fraction(0, 1),
            Fraction(10, 1),
            Fraction(10, 1),
            Fraction(20, 1),
        )
        self.assertEqual(res, Fraction(15, 1))

    def test_interpolar_linear_racional_pontos_coincidentes(self):
        res = interpolar_linear_racional(
            Fraction(5, 1),
            Fraction(10, 1),
            Fraction(42, 1),
            Fraction(10, 1),
            Fraction(42, 1),
        )
        self.assertEqual(res, Fraction(42, 1))

    def test_relacao_ac_resistencia_ponto_exato_tabela(self):
        # CP_II_32: a/c = 0.50 -> fcm = 32
        ac = calcular_relacao_ac_resistencia(Fraction(32, 1), TipoCimento.CP_II_32)
        self.assertEqual(ac, Fraction(50, 100))

    def test_relacao_ac_resistencia_interpolacao_intermediaria(self):
        # CP_II_32: a/c=0.50 -> 32, a/c=0.55 -> 28. fcm=30 está no ponto médio -> a/c=0.525
        ac = calcular_relacao_ac_resistencia(Fraction(30, 1), TipoCimento.CP_II_32)
        self.assertEqual(ac, Fraction(105, 200))
        self.assertEqual(float(ac), 0.525)

    def test_relacao_ac_resistencia_extrapolacao_superior(self):
        # fcm muito baixo (10 MPa), extrapola além de 0.75 mas respeita limite prático
        ac = calcular_relacao_ac_resistencia(Fraction(10, 1), TipoCimento.CP_II_32)
        self.assertGreaterEqual(ac, Fraction(75, 100))
        self.assertLessEqual(ac, Fraction(85, 100))

    def test_relacao_ac_resistencia_extrapolacao_inferior(self):
        # fcm muito alto (70 MPa), extrapola abaixo de 0.35 mas respeita limite prático
        ac = calcular_relacao_ac_resistencia(Fraction(70, 1), TipoCimento.CP_II_32)
        self.assertLessEqual(ac, Fraction(35, 100))
        self.assertGreaterEqual(ac, Fraction(25, 100))

    def test_relacao_ac_curva_personalizada(self):
        curva_custom = (
            (Fraction(40, 100), Fraction(40, 1)),
            (Fraction(60, 100), Fraction(20, 1)),
        )
        # fcm = 30 -> a/c = 0.50
        ac = calcular_relacao_ac_resistencia(
            Fraction(30, 1),
            TipoCimento.PERSONALIZADO,
            curva_personalizada=curva_custom,
        )
        self.assertEqual(ac, Fraction(50, 100))

    def test_consumo_agua_ponto_exato(self):
        # Slump 70 mm, Brita 19 mm -> tabela exata = 200 L, ar = 20 L
        agua, ar = calcular_consumo_agua(70, Fraction(19, 1))
        self.assertEqual(agua, Fraction(200, 1))
        self.assertEqual(ar, Fraction(20, 1))

    def test_consumo_agua_com_aditivo_plastificante(self):
        # Redução de 10% em 200 L -> 180 L
        agua, _ = calcular_consumo_agua(
            70,
            Fraction(19, 1),
            aditivo_redutor_agua_pct=Fraction(10, 1),
        )
        self.assertEqual(agua, Fraction(180, 1))

    def test_volume_aparente_brita_ponto_exato(self):
        # Brita 19 mm, MF 2.40 -> tabela = 0.67
        v_ob = calcular_volume_aparente_brita(Fraction(19, 1), Fraction(24, 10))
        self.assertEqual(v_ob, Fraction(67, 100))

    def test_volume_aparente_brita_interpolado(self):
        # Brita 19 mm, MF 2.50 (entre 2.40 com 0.67 e 2.60 com 0.65) -> 0.66
        v_ob = calcular_volume_aparente_brita(Fraction(19, 1), Fraction(25, 10))
        self.assertEqual(v_ob, Fraction(66, 100))

    def test_calcular_custos_zero_precos(self):
        consumos = ConsumosMetroCubico(
            cimento_kg=Fraction(350, 1),
            agua_litros=Fraction(180, 1),
            areia_kg=Fraction(750, 1),
            britas_kg=(("Brita 1", Fraction(1000, 1)),),
            brita_total_kg=Fraction(1000, 1),
            aditivo_kg=Fraction(0, 1),
            ar_aprisionado_litros=Fraction(20, 1),
            volume_cimento_litros=Fraction(111, 1),
            volume_agua_litros=Fraction(180, 1),
            volume_areia_litros=Fraction(285, 1),
            volumes_brita_litros=(("Brita 1", Fraction(375, 1)),),
            volume_brita_total_litros=Fraction(375, 1),
            volume_aditivo_litros=Fraction(0, 1),
            volume_absoluto_total_litros=Fraction(1000, 1),
            massa_especifica_fresca_kg_m3=Fraction(2280, 1),
            sacos_cimento_50kg=Fraction(7, 1),
        )
        precos_zerados = PrecosUnitarios()
        custo = calcular_custos(consumos, precos_zerados)
        self.assertEqual(custo.custo_total_m3, Fraction(0))
        self.assertEqual(custo.custo_por_saco_cimento, Fraction(0))

    def test_calcular_dosagem_abcp_fecha_exatamente_1000_litros(self):
        params = ParametrosDosagem(
            identificacao="Teste 1000L",
            fck_mpa=Fraction(25, 1),
            condicao_preparo=CondicaoPreparo.A,
            classe_agressividade=ClasseAgressividadeAmbiental.CAA_II,
            tipo_estrutura=TipoEstrutura.CONCRETO_ARMADO,
            slump_mm=80,
            cimento=Cimento(tipo=TipoCimento.CP_II_32),
            areia=AgregadoMiudo(
                nome="Areia",
                modulo_finura=Fraction(24, 10),
                massa_especifica_real_kg_l=Fraction(265, 100),
            ),
            britas=(
                AgregadoGraudo(
                    nome="Brita 1",
                    d_max_mm=Fraction(19, 1),
                    massa_unitaria_compactada_kg_m3=Fraction(1500, 1),
                    massa_especifica_real_kg_l=Fraction(268, 100),
                ),
            ),
        )
        res = calcular_dosagem_abcp(params)
        self.assertEqual(res.consumos_m3.volume_absoluto_total_litros, Fraction(1000, 1))
        self.assertGreater(res.consumos_m3.cimento_kg, Fraction(280, 1))
        self.assertGreater(res.consumos_m3.areia_kg, Fraction(500, 1))
        self.assertGreater(res.consumos_m3.brita_total_kg, Fraction(800, 1))

    def test_elevacao_cimento_por_minimo_caa(self):
        # Exigir CAA IV (mínimo de cimento 360 kg/m³, máx a/c 0.45)
        params = ParametrosDosagem(
            identificacao="Teste CAA IV",
            fck_mpa=Fraction(40, 1),
            condicao_preparo=CondicaoPreparo.A,
            classe_agressividade=ClasseAgressividadeAmbiental.CAA_IV,
            tipo_estrutura=TipoEstrutura.CONCRETO_ARMADO,
            slump_mm=40,
            cimento=Cimento(tipo=TipoCimento.CP_V_ARI),
            areia=AgregadoMiudo(
                nome="Areia",
                modulo_finura=Fraction(26, 10),
                massa_especifica_real_kg_l=Fraction(265, 100),
            ),
            britas=(
                AgregadoGraudo(
                    nome="Brita 2",
                    d_max_mm=Fraction(25, 1),
                    massa_unitaria_compactada_kg_m3=Fraction(1520, 1),
                    massa_especifica_real_kg_l=Fraction(268, 100),
                ),
            ),
        )
        res = calcular_dosagem_abcp(params)
        self.assertGreaterEqual(res.consumos_m3.cimento_kg, Fraction(360, 1))
        self.assertLessEqual(res.verificacoes.ac_adotado, Fraction(9, 20))


if __name__ == "__main__":
    unittest.main()
