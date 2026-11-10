"""Testes para geração de pacotes determinísticos ZIP.

LOFRANO TECNOLOGIA.
"""

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
import zipfile

from dosagem_concreto_abcp.errors import ErroExportacao
from dosagem_concreto_abcp.packaging import (
    DATA_HORA_FIXA,
    gerar_bytes_zip_deterministico,
    salvar_zip_deterministico,
)


class TestPackaging(unittest.TestCase):
    def test_gerar_bytes_zip_deterministico_invariante(self):
        arquivos = {
            "b.txt": "conteúdo B\n",
            "a.txt": "conteúdo A\n",
            "dados.json": '{"status": "ok"}\n',
        }
        b1 = gerar_bytes_zip_deterministico(arquivos)
        b2 = gerar_bytes_zip_deterministico(arquivos)

        # Mesmos bytes exatos
        self.assertEqual(b1, b2)
        self.assertEqual(sha256(b1).hexdigest(), sha256(b2).hexdigest())

    def test_zip_contem_data_hora_fixa_e_permissao(self):
        arquivos = {"teste.txt": "teste"}
        bytes_zip = gerar_bytes_zip_deterministico(arquivos)

        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            tmp.write(bytes_zip)
            tmp.flush()

            with zipfile.ZipFile(tmp.name, "r") as zf:
                info = zf.getinfo("teste.txt")
                self.assertEqual(info.date_time, DATA_HORA_FIXA)
                # Permissão 0o100644 nos 16 bits superiores
                self.assertEqual(info.external_attr >> 16, 0o100644)

    def test_salvar_zip_nao_sobrescreve_sem_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p_zip = Path(tmpdir) / "teste.zip"
            p_zip.write_bytes(b"existente")

            with self.assertRaises(ErroExportacao):
                salvar_zip_deterministico(
                    p_zip,
                    {"arquivo.txt": "novo"},
                    sobrescrever=False,
                )

    def test_salvar_zip_sobrescreve_com_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p_zip = Path(tmpdir) / "teste.zip"
            p_zip.write_bytes(b"existente")

            h = salvar_zip_deterministico(
                p_zip,
                {"arquivo.txt": "novo"},
                sobrescrever=True,
            )
            self.assertTrue(p_zip.exists())
            self.assertEqual(sha256(p_zip.read_bytes()).hexdigest(), h)


if __name__ == "__main__":
    unittest.main()
