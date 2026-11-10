"""Geração determinística de pacotes ZIP para casos de dosagem de concreto.

LOFRANO TECNOLOGIA.
Data e hora padronizadas (2026-01-01 00:00:00), permissões estritas (0o100644) e escrita atômica/exclusiva.
"""

from hashlib import sha256
import io
import os
from pathlib import Path
import zipfile

from .errors import ErroExportacao

DATA_HORA_FIXA: tuple[int, int, int, int, int, int] = (2026, 1, 1, 0, 0, 0)
PERMISSAO_PADRAO: int = 0o100644


def gerar_bytes_zip_deterministico(arquivos: dict[str, bytes | str]) -> bytes:
    """Empacota os arquivos fornecidos em um arquivo ZIP com ordenação canônica e atributos invariantes."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for nome_arquivo in sorted(arquivos.keys()):
            conteudo = arquivos[nome_arquivo]
            if isinstance(conteudo, str):
                dados = conteudo.encode("utf-8")
            else:
                dados = conteudo

            info = zipfile.ZipInfo(filename=nome_arquivo, date_time=DATA_HORA_FIXA)
            info.external_attr = PERMISSAO_PADRAO << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, dados)

    return buffer.getvalue()


def salvar_zip_deterministico(
    caminho_destino: Path,
    arquivos: dict[str, bytes | str],
    sobrescrever: bool = False,
) -> str:
    """Salva pacote ZIP determinístico no caminho indicado.

    Retorna o hash SHA-256 do arquivo gerado.
    """
    bytes_zip = gerar_bytes_zip_deterministico(arquivos)
    hash_sha256 = sha256(bytes_zip).hexdigest()

    p = Path(caminho_destino)
    if p.exists() and not sobrescrever:
        raise ErroExportacao(f"Arquivo de destino '{p}' já existe e sobrescrita não foi habilitada.")

    flags = os.O_CREAT | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    if not sobrescrever:
        flags |= os.O_EXCL
    else:
        flags |= os.O_TRUNC

    try:
        fd = os.open(p, flags, 0o644)
        with os.fdopen(fd, "wb") as f:
            f.write(bytes_zip)
    except OSError as e:
        raise ErroExportacao(f"Falha ao gravar pacote ZIP em '{p}': {e}") from e

    return hash_sha256
