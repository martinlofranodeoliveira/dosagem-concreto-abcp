#!/usr/bin/env python3
"""Verifica integridade dos pacotes wheel e sdist construídos fora da árvore de código.

LOFRANO TECNOLOGIA.
"""

import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile


def verificar_distribuicao() -> None:
    raiz = Path(__file__).resolve().parent.parent
    dist_dir = raiz / "dist"

    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))

    if not wheels:
        raise FileNotFoundError("Nenhum arquivo wheel (.whl) encontrado em dist/")
    if not sdists:
        raise FileNotFoundError("Nenhum arquivo sdist (.tar.gz) encontrado em dist/")

    wheel = wheels[0]
    sdist = sdists[0]

    print(f"[*] Inspecionando wheel: {wheel.name}")
    with zipfile.ZipFile(wheel, "r") as zf:
        membros_wheel = zf.namelist()
        print(f"    - Membros no wheel: {len(membros_wheel)}")
        for m in membros_wheel:
            print(f"      • {m}")

    print(f"[*] Inspecionando sdist: {sdist.name}")
    with tarfile.open(sdist, "r:gz") as tf:
        membros_sdist = tf.getnames()
        print(f"    - Membros no sdist: {len(membros_sdist)}")

    # Testar instalação e execução fora da árvore em ambiente temporário
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        print(f"[*] Testando execução isolada fora da árvore de código em: {tmp_p}")
        cmd_install = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(tmp_p),
            str(wheel.resolve()),
        ]
        subprocess.run(cmd_install, check=True, capture_output=True)

        # Testar importação a partir do diretório isolado com ambiente limpo (sem PYTHONPATH)
        env_limpo = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        cmd_test = [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); import dosagem_concreto_abcp; print('Importado com sucesso:', dosagem_concreto_abcp.__version__)",
            str(tmp_p),
        ]
        try:
            res = subprocess.run(cmd_test, check=True, capture_output=True, text=True, env=env_limpo)
            print(f"[OK] {res.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"FALHA NA IMPORTAÇÃO ISOLADA:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}", file=sys.stderr)
            raise


if __name__ == "__main__":
    try:
        verificar_distribuicao()
        sys.exit(0)
    except Exception as e:
        print(f"FALHA NA VERIFICAÇÃO DE DISTRIBUIÇÃO: {e}", file=sys.stderr)
        sys.exit(1)
