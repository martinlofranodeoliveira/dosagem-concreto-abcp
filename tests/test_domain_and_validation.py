"""Testes de validação de limites físicos, normativos e modelos de domínio.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from dosagem_concreto_abcp.calculator import validar_parametros
from dosagem_concreto_abcp.domain import (
    AgregadoGraudo,
    AgregadoMiudo,
    Cimento,
    ClasseAgressividadeAmbiental,
    CondicaoPreparo,
    ParametrosDosagem,
    TipoCimento,
    TipoEstrutura,
)
from dosagem_concreto_abcp.errors import (
    ErroAgregadoInvalido,
    ErroCondicaoPreparoIncompativel,
    ErroResistenciaInvalida,
    ErroSlumpInvalido,
    ErroValidacaoParametros,
)


class TestDomainAndValidation(unittest.TestCase):
    def criar_parametros_base(self, **kwargs) -> ParametrosDosagem:
        dados = {
            "identificacao": "Caso Padrão Teste",
            "fck_mpa": Fraction(25, 1),
            "condicao_preparo": CondicaoPreparo.A,
            "classe_agressividade": ClasseAgressividadeAmbiental.CAA_II,
            "tipo_estrutura": TipoEstrutura.CONCRETO_ARMADO,
            "slump_mm": 80,
            "cimento": Cimento(tipo=TipoCimento.CP_II_32),
            "areia": AgregadoMiudo(
                nome="Areia Média",
                modulo_finura=Fraction(24, 10),
                massa_especifica_real_kg_l=Fraction(265, 100),
            ),
            "britas": (
                AgregadoGraudo(
                    nome="Brita 1",
                    d_max_mm=Fraction(19, 1),
                    massa_unitaria_compactada_kg_m3=Fraction(1500, 1),
                    massa_especifica_real_kg_l=Fraction(268, 100),
                ),
            ),
        }
        dados.update(kwargs)
        return ParametrosDosagem(**dados)

    def test_parametros_validos_passam_sem_erro(self):
        p = self.criar_parametros_base()
        validar_parametros(p)

    def test_fck_menor_que_10_rejeitado(self):
        p = self.criar_parametros_base(fck_mpa=Fraction(9, 1))
        with self.assertRaises(ErroResistenciaInvalida):
            validar_parametros(p)

    def test_fck_maior_que_100_rejeitado(self):
        p = self.criar_parametros_base(fck_mpa=Fraction(105, 1))
        with self.assertRaises(ErroResistenciaInvalida):
            validar_parametros(p)

    def test_condicao_c_com_fck_maior_que_15_rejeitada(self):
        p = self.criar_parametros_base(
            fck_mpa=Fraction(16, 1),
            condicao_preparo=CondicaoPreparo.C,
        )
        with self.assertRaises(ErroCondicaoPreparoIncompativel):
            validar_parametros(p)

    def test_condicao_c_com_fck_15_permitida(self):
        p = self.criar_parametros_base(
            fck_mpa=Fraction(15, 1),
            condicao_preparo=CondicaoPreparo.C,
            classe_agressividade=ClasseAgressividadeAmbiental.CAA_I,
        )
        validar_parametros(p)

    def test_condicao_b_com_fck_maior_que_25_rejeitada(self):
        p = self.criar_parametros_base(
            fck_mpa=Fraction(30, 1),
            condicao_preparo=CondicaoPreparo.B,
        )
        with self.assertRaises(ErroCondicaoPreparoIncompativel):
            validar_parametros(p)

    def test_slump_menor_que_30_rejeitado(self):
        p = self.criar_parametros_base(slump_mm=25)
        with self.assertRaises(ErroSlumpInvalido):
            validar_parametros(p)

    def test_slump_maior_que_180_rejeitado(self):
        p = self.criar_parametros_base(slump_mm=200)
        with self.assertRaises(ErroSlumpInvalido):
            validar_parametros(p)

    def test_sem_brita_rejeitado(self):
        p = self.criar_parametros_base(britas=())
        with self.assertRaises(ErroAgregadoInvalido):
            validar_parametros(p)

    def test_brita_com_dmax_negativo_rejeitado(self):
        brita_invalida = AgregadoGraudo(
            nome="Brita Negativa",
            d_max_mm=Fraction(-19, 1),
            massa_unitaria_compactada_kg_m3=Fraction(1500, 1),
            massa_especifica_real_kg_l=Fraction(268, 100),
        )
        p = self.criar_parametros_base(britas=(brita_invalida,))
        with self.assertRaises(ErroAgregadoInvalido):
            validar_parametros(p)

    def test_brita_com_massa_unitaria_negativa_rejeitada(self):
        brita_invalida = AgregadoGraudo(
            nome="Brita Unitária Negativa",
            d_max_mm=Fraction(19, 1),
            massa_unitaria_compactada_kg_m3=Fraction(-1500, 1),
            massa_especifica_real_kg_l=Fraction(268, 100),
        )
        p = self.criar_parametros_base(britas=(brita_invalida,))
        with self.assertRaises(ErroAgregadoInvalido):
            validar_parametros(p)

    def test_areia_com_modulo_finura_fora_da_faixa_rejeitada(self):
        areia_muito_fina = AgregadoMiudo(
            nome="Areia Fina Demais",
            modulo_finura=Fraction(15, 10),  # < 1.80
            massa_especifica_real_kg_l=Fraction(265, 100),
        )
        p = self.criar_parametros_base(areia=areia_muito_fina)
        with self.assertRaises(ErroAgregadoInvalido):
            validar_parametros(p)

        areia_muito_grossa = AgregadoMiudo(
            nome="Areia Grossa Demais",
            modulo_finura=Fraction(38, 10),  # > 3.60
            massa_especifica_real_kg_l=Fraction(265, 100),
        )
        p2 = self.criar_parametros_base(areia=areia_muito_grossa)
        with self.assertRaises(ErroAgregadoInvalido):
            validar_parametros(p2)

    def test_cimento_com_massa_especifica_invalida_rejeitado(self):
        cim = Cimento(
            tipo=TipoCimento.CP_II_32,
            massa_especifica_real_kg_l=Fraction(-3, 1),
        )
        p = self.criar_parametros_base(cimento=cim)
        with self.assertRaises(ErroValidacaoParametros):
            validar_parametros(p)


if __name__ == "__main__":
    unittest.main()
