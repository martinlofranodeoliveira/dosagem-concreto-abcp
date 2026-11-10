"""Formatadores numéricos e textuais determinísticos em português (pt-BR).

LOFRANO TECNOLOGIA.
Todos os cálculos de arredondamento e conversão de frações são estritamente inteiros. Ponto flutuante é proibido.
"""

from fractions import Fraction
from typing import Sequence
from .domain import TracoMassa, AjusteCanteiro, ConsumosMetroCubico, CustoConcreto


def formatar_fracao_decimal(
    valor: Fraction | int,
    casas: int = 2,
    separador_milhar: bool = False,
) -> str:
    """Converte Fraction ou int para string decimal formatada no padrão brasileiro (vírgula).

    O arredondamento utiliza a regra da metade para cima (half-up) inteiramente em inteiros.
    """
    if isinstance(valor, int):
        f = Fraction(valor, 1)
    else:
        f = valor

    if f == 0:
        if casas > 0:
            return "0," + "0" * casas
        return "0"

    negativo = f < 0
    num = abs(f.numerator)
    den = abs(f.denominator)

    # Multiplica pelo fator da potência de 10
    fator = 10**casas
    # Arredondamento half-up: (num * fator * 2 + den) // (2 * den)
    valor_arredondado = (num * fator * 2 + den) // (2 * den)

    parte_inteira = valor_arredondado // fator
    parte_fracionaria = valor_arredondado % fator

    # Formatar parte inteira com separador de milhar se solicitado
    str_inteira = str(parte_inteira)
    if separador_milhar and len(str_inteira) > 3:
        blocos: list[str] = []
        n = len(str_inteira)
        primeiro = n % 3
        if primeiro > 0:
            blocos.append(str_inteira[:primeiro])
        for i in range(primeiro, n, 3):
            blocos.append(str_inteira[i : i + 3])
        str_inteira = ".".join(blocos)

    prefixo = "-" if negativo and valor_arredondado > 0 else ""

    if casas == 0:
        return f"{prefixo}{str_inteira}"

    str_fracionaria = str(parte_fracionaria).zfill(casas)
    return f"{prefixo}{str_inteira},{str_fracionaria}"


def formatar_moeda(valor: Fraction | int) -> str:
    """Formata valor monetário no padrão brasileiro R$ #.##0,00."""
    return f"R$ {formatar_fracao_decimal(valor, casas=2, separador_milhar=True)}"


def formatar_traco_unitario(traco: TracoMassa) -> str:
    """Formata traço unitário em massa seca: 1 : areia : brita : a/c."""
    str_areia = formatar_fracao_decimal(traco.areia, casas=2)
    if len(traco.britas) == 1:
        str_brita = formatar_fracao_decimal(traco.brita_total, casas=2)
    else:
        partes_brita = [
            f"{formatar_fracao_decimal(b[1], casas=2)} ({b[0]})"
            for b in traco.britas
        ]
        str_brita = f"{formatar_fracao_decimal(traco.brita_total, casas=2)} [{' + '.join(partes_brita)}]"
    str_ac = formatar_fracao_decimal(traco.agua_cimento, casas=2)
    return f"1 : {str_areia} : {str_brita} : {str_ac}"


def formatar_traco_saco_50kg(ajuste: AjusteCanteiro) -> str:
    """Formata proporção por saco de cimento de 50 kg para canteiro de obras."""
    cimento = formatar_fracao_decimal(ajuste.traco_saco_50kg_cimento_kg, casas=1)
    areia = formatar_fracao_decimal(ajuste.traco_saco_50kg_areia_umida_kg, casas=1)
    if len(ajuste.traco_saco_50kg_britas_umidas_kg) == 1:
        brita = formatar_fracao_decimal(ajuste.traco_saco_50kg_britas_umidas_kg[0][1], casas=1)
        str_brita = f"{brita} kg de brita"
    else:
        partes = [
            f"{formatar_fracao_decimal(b[1], casas=1)} kg ({b[0]})"
            for b in ajuste.traco_saco_50kg_britas_umidas_kg
        ]
        str_brita = " + ".join(partes)
    agua = formatar_fracao_decimal(ajuste.traco_saco_50kg_agua_litros, casas=1)
    return (
        f"{cimento} kg cimento (1 saco) : {areia} kg areia úmida : {str_brita} : "
        f"{agua} L de água a adicionar"
    )
