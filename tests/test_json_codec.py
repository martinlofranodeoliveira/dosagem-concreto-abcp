"""Testes para o codec JSON canônico com banimento de ponto flutuante e validações de segurança.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import json
import unittest

from dosagem_concreto_abcp.domain import CondicaoPreparo
from dosagem_concreto_abcp.errors import ErroCodecJson
from dosagem_concreto_abcp.json_codec import (
    carregar_parametros_json,
    converter_fracao,
    decodificar_json_seguro,
    serializar_json_canonico,
    validar_profundidade,
)


class TestJsonCodec(unittest.TestCase):
    def test_rejeicao_ponto_flutuante_imediata(self):
        json_com_float = '{"fck": 25.5}'
        with self.assertRaises(ErroCodecJson) as ctx:
            decodificar_json_seguro(json_com_float)
        self.assertIn("Ponto flutuante proibido", str(ctx.exception))

    def test_rejeicao_bom_utf8_em_bytes(self):
        dados_com_bom = b"\xef\xbb\xbf{\"fck\": 25}"
        with self.assertRaises(ErroCodecJson) as ctx:
            decodificar_json_seguro(dados_com_bom)
        self.assertIn("BOM UTF-8 proibido", str(ctx.exception))

    def test_rejeicao_bom_utf8_em_str(self):
        texto_com_bom = "\ufeff{\"fck\": 25}"
        with self.assertRaises(ErroCodecJson) as ctx:
            decodificar_json_seguro(texto_com_bom)
        self.assertIn("BOM UTF-8 proibido", str(ctx.exception))

    def test_rejeicao_chaves_duplicadas(self):
        json_chaves_duplicadas = '{"chave": 1, "chave": 2}'
        with self.assertRaises(ErroCodecJson) as ctx:
            decodificar_json_seguro(json_chaves_duplicadas)
        self.assertIn("Chave duplicada proibida", str(ctx.exception))

    def test_rejeicao_profundidade_excessiva(self):
        obj: dict = {}
        curr = obj
        for _ in range(35):
            curr["filho"] = {}
            curr = curr["filho"]

        with self.assertRaises(ErroCodecJson) as ctx:
            validar_profundidade(obj, limite_max=32)
        self.assertIn("Profundidade estrutural excessiva", str(ctx.exception))

    def test_converter_fracao_aceita_int_str_fraction(self):
        self.assertEqual(converter_fracao(25), Fraction(25, 1))
        self.assertEqual(converter_fracao("25"), Fraction(25, 1))
        self.assertEqual(converter_fracao("25/2"), Fraction(25, 2))
        self.assertEqual(converter_fracao("25.5"), Fraction(255, 10))
        self.assertEqual(converter_fracao("25,5"), Fraction(255, 10))
        self.assertEqual(converter_fracao(Fraction(3, 4)), Fraction(3, 4))

    def test_converter_fracao_rejeita_float_explicitamente(self):
        with self.assertRaises(ErroCodecJson):
            converter_fracao(25.5)

    def test_serializar_json_canonico_determinismo_e_newline(self):
        dado = {"b": 2, "a": 1, "c": [3, 2, 1]}
        texto = serializar_json_canonico(dado)
        self.assertTrue(texto.endswith("\n"))
        # As chaves devem estar ordenadas 'a' antes de 'b'
        self.assertLess(texto.index('"a"'), texto.index('"b"'))

    def test_carregar_parametros_json_valido(self):
        modelo = {
            "identificacao": "Teste Codec",
            "fck_mpa": 25,
            "condicao_preparo": "A",
            "classe_agressividade": "CAA_II",
            "tipo_estrutura": "CONCRETO_ARMADO",
            "slump_mm": 80,
            "cimento": {
                "tipo": "CP_II_32",
                "massa_especifica_real_kg_l": "3.15",
            },
            "areia": {
                "nome": "Areia",
                "modulo_finura": "2.40",
                "massa_especifica_real_kg_l": "2.65",
            },
            "britas": [
                {
                    "nome": "Brita 1",
                    "d_max_mm": "19.0",
                    "massa_unitaria_compactada_kg_m3": 1500,
                    "massa_especifica_real_kg_l": "2.68",
                }
            ],
        }
        params = carregar_parametros_json(modelo)
        self.assertEqual(params.fck_mpa, Fraction(25, 1))
        self.assertEqual(params.condicao_preparo, CondicaoPreparo.A)
        self.assertEqual(params.slump_mm, 80)


if __name__ == "__main__":
    unittest.main()
