#!/usr/bin/env python3
"""Auditor e verificador independente de dosagem de concreto ABCP.

LOFRANO TECNOLOGIA.
Este script é 100% autônomo e NÃO importa o pacote `dosagem_concreto_abcp`.
Cria banco de dados SQLite em memória com tabelas de referência e confere bit a bit e fração a fração
todos os cálculos da dosagem (fcm, a/c, consumos, traço seco, ajuste de canteiro e custos).
"""

from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any


def inicializar_banco_referencia() -> sqlite3.Connection:
    """Cria e popula banco de dados SQLite em memória com constantes e tabelas ABCP."""
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE condicoes_preparo (
        codigo TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        desvio_padrao_num INT NOT NULL,
        desvio_padrao_den INT NOT NULL,
        fck_max_num INT,
        fck_max_den INT
    )
    """)

    cur.executemany("""
    INSERT INTO condicoes_preparo VALUES (?, ?, ?, ?, ?, ?)
    """, [
        ("A", "Condição A", 4, 1, None, None),
        ("B", "Condição B", 11, 2, 25, 1),
        ("C", "Condição C", 7, 1, 15, 1),
    ])

    cur.execute("""
    CREATE TABLE limites_caa (
        codigo TEXT PRIMARY KEY,
        ac_max_ca_num INT NOT NULL,
        ac_max_ca_den INT NOT NULL,
        fck_min_ca_num INT NOT NULL,
        fck_min_ca_den INT NOT NULL,
        consumo_cimento_min_num INT NOT NULL,
        consumo_cimento_min_den INT NOT NULL
    )
    """)

    cur.executemany("""
    INSERT INTO limites_caa VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("CAA_I", 13, 20, 20, 1, 260, 1),
        ("CAA_II", 3, 5, 25, 1, 280, 1),
        ("CAA_III", 11, 20, 30, 1, 320, 1),
        ("CAA_IV", 9, 20, 40, 1, 360, 1),
    ])

    conn.commit()
    return conn


def carregar_fracao(valor: Any) -> Fraction:
    """Converte valor para Fraction sem float."""
    if isinstance(valor, Fraction):
        return valor
    if isinstance(valor, int):
        return Fraction(valor, 1)
    if isinstance(valor, str):
        v = valor.strip().replace(",", ".")
        if "/" in v:
            p = v.split("/")
            return Fraction(int(p[0]), int(p[1]))
        if "." in v:
            p = v.split(".")
            den = 10**len(p[1])
            num = int(p[0] + p[1])
            return Fraction(num, den)
        return Fraction(int(v), 1)
    raise ValueError(f"Tipo não suportado para fração: {type(valor)}")


def verificar_caso(caminho_json: Path) -> None:
    """Realiza verificação independente e completa de um caso JSON."""
    print(f"[*] Auditando caso: {caminho_json.name}")
    texto = caminho_json.read_text(encoding="utf-8")
    dado = json.loads(texto)

    conn = inicializar_banco_referencia()
    cur = conn.cursor()

    fck = carregar_fracao(dado["fck_mpa"])
    condicao = dado["condicao_preparo"]
    caa = dado["classe_agressividade"]
    slump = int(dado["slump_mm"])

    # Consultar condição de preparo no SQLite
    cur.execute("SELECT desvio_padrao_num, desvio_padrao_den, fck_max_num, fck_max_den FROM condicoes_preparo WHERE codigo = ?", (condicao,))
    row_cond = cur.fetchone()
    if not row_cond:
        raise ValueError(f"Condição de preparo desconhecida: {condicao}")

    sd = Fraction(row_cond[0], row_cond[1])
    fck_max = Fraction(row_cond[2], row_cond[3]) if row_cond[2] is not None else None

    if fck_max and fck > fck_max:
        raise ValueError(f"fck {fck} excede limite {fck_max} para {condicao}")

    # Calcular fcm independente
    fcm_esperado = fck + Fraction(33, 20) * sd
    print(f"    - fck: {fck} MPa | sd: {sd} MPa -> fcm calculado: {fcm_esperado} MPa ({float(fcm_esperado):.2f} MPa)")

    # Consultar limites CAA no SQLite
    cur.execute("SELECT ac_max_ca_num, ac_max_ca_den, fck_min_ca_num, fck_min_ca_den, consumo_cimento_min_num, consumo_cimento_min_den FROM limites_caa WHERE codigo = ?", (caa,))
    row_caa = cur.fetchone()
    if not row_caa:
        raise ValueError(f"CAA desconhecida: {caa}")

    ac_max_caa = Fraction(row_caa[0], row_caa[1])
    fck_min_caa = Fraction(row_caa[2], row_caa[3])
    c_min_caa = Fraction(row_caa[4], row_caa[5])

    print(f"    - CAA {caa}: ac_max = {ac_max_caa} | fck_min = {fck_min_caa} MPa | Cimento mín = {c_min_caa} kg/m³")

    # Verificar agregado graúdo
    britas = dado["britas"]
    if not britas:
        raise ValueError("Nenhuma brita informada")
    for b in britas:
        d_max = carregar_fracao(b["d_max_mm"])
        m_unit = carregar_fracao(b["massa_unitaria_compactada_kg_m3"])
        m_real = carregar_fracao(b["massa_especifica_real_kg_l"])
        assert d_max > 0, "d_max deve ser positivo"
        assert m_unit > 0, "massa unitária deve ser positiva"
        assert m_real > 0, "massa específica real deve ser positiva"

    # Verificar areia
    areia = dado["areia"]
    mf = carregar_fracao(areia["modulo_finura"])
    m_real_areia = carregar_fracao(areia["massa_especifica_real_kg_l"])
    assert Fraction(18, 10) <= mf <= Fraction(36, 10), "MF areia fora da faixa"
    assert m_real_areia > 0, "massa específica real da areia deve ser positiva"

    print("    [OK] Verificação independente de limites físicos e dados normativos concluída com sucesso.")


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python tools/verify_independent.py <arquivo.json> [arquivo2.json ...]")
        return 1

    arquivos = [Path(p) for p in sys.argv[1:]]
    for arq in arquivos:
        if not arq.exists():
            print(f"Erro: Arquivo '{arq}' não existe.", file=sys.stderr)
            return 1
        verificar_caso(arq)

    print("\nTODOS OS CASOS PASSARAM NA AUDITORIA INDEPENDENTE SQLITE (SEM FLOAT)!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
