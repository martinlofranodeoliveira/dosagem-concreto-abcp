"""Testes de ponta a ponta da CLI de dosagem de concreto.

LOFRANO TECNOLOGIA.
"""

from pathlib import Path
import tempfile
import unittest

from dosagem_concreto_abcp.cli import main


class TestCli(unittest.TestCase):
    def setUp(self):
        self.raiz = Path(__file__).resolve().parent.parent
        self.exemplar = self.raiz / "exemplares" / "caso_c25_obra_urbana.json"

    def test_cli_sem_argumentos_retorna_1(self):
        codigo = main([])
        self.assertEqual(codigo, 1)

    def test_cli_versao_retorna_0(self):
        codigo = main(["versao"])
        self.assertEqual(codigo, 0)

    def test_cli_tabelas_retorna_0(self):
        codigo = main(["tabelas"])
        self.assertEqual(codigo, 0)

    def test_cli_modelo_stdout_retorna_0(self):
        codigo = main(["modelo"])
        self.assertEqual(codigo, 0)

    def test_cli_modelo_arquivo_retorna_0(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            codigo = main(["modelo", "--saida", tmp.name])
            self.assertEqual(codigo, 0)
            conteudo = Path(tmp.name).read_text(encoding="utf-8")
            self.assertIn("fck_mpa", conteudo)

    def test_cli_calcular_arquivo_inexistente_retorna_1(self):
        codigo = main(["calcular", "/caminho/inexistente/caso.json"])
        self.assertEqual(codigo, 1)

    def test_cli_calcular_sucesso_com_todas_as_saidas(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            p_json = dir_path / "saida.json"
            p_md = dir_path / "saida.md"
            p_csv = dir_path / "saida.csv"
            p_svg = dir_path / "saida.svg"
            p_zip = dir_path / "saida.zip"

            args = [
                "calcular",
                str(self.exemplar),
                "--saida-json",
                str(p_json),
                "--saida-md",
                str(p_md),
                "--saida-csv",
                str(p_csv),
                "--saida-svg",
                str(p_svg),
                "--saida-zip",
                str(p_zip),
                "--sobrescrever",
            ]
            codigo = main(args)
            self.assertEqual(codigo, 0)

            self.assertTrue(p_json.exists())
            self.assertTrue(p_md.exists())
            self.assertTrue(p_csv.exists())
            self.assertTrue(p_svg.exists())
            self.assertTrue(p_zip.exists())

            self.assertIn('"identificacao"', p_json.read_text(encoding="utf-8"))
            self.assertIn("# Memorial", p_md.read_text(encoding="utf-8"))
            self.assertIn(";", p_csv.read_text(encoding="utf-8"))
            self.assertIn("<svg", p_svg.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
