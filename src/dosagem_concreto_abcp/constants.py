"""Constantes, tabelas empíricas e limites normativos da ABNT NBR 12655 e NBR 6118.

LOFRANO TECNOLOGIA.
Todos os coeficientes numéricos são expressos como frações exatas (Fraction) ou inteiros.
"""

from __future__ import annotations

from fractions import Fraction
from typing import NamedTuple

# Coeficiente estatístico para 5% de probabilidade de resultados inferiores ao fck
FATOR_QUANTIL_NORMAL: Fraction = Fraction(33, 20)  # 1,65


class RegraCondicaoPreparo(NamedTuple):
    """Regra de desvio-padrão e limites de fck para condição de preparo (NBR 12655:2022)."""
    nome: str
    desvio_padrao_mpa: Fraction
    fck_min_mpa: Fraction
    fck_max_mpa: Fraction | None
    descricao: str


REGRAS_CONDICAO_PREPARO: dict[str, RegraCondicaoPreparo] = {
    "A": RegraCondicaoPreparo(
        nome="Condição A",
        desvio_padrao_mpa=Fraction(4, 1),  # 4,0 MPa
        fck_min_mpa=Fraction(10, 1),
        fck_max_mpa=None,
        descricao=(
            "Cimento e agregados medidos em massa; água de amassamento medida em volume ou massa "
            "com correção rigorosa em função da umidade dos agregados."
        ),
    ),
    "B": RegraCondicaoPreparo(
        nome="Condição B",
        desvio_padrao_mpa=Fraction(11, 2),  # 5,5 MPa
        fck_min_mpa=Fraction(10, 1),
        fck_max_mpa=Fraction(25, 1),  # Limite máximo de fck para condição B
        descricao=(
            "Cimento medido em massa; agregados medidos em volume; água de amassamento corrigida "
            "em função da umidade da areia."
        ),
    ),
    "C": RegraCondicaoPreparo(
        nome="Condição C",
        desvio_padrao_mpa=Fraction(7, 1),  # 7,0 MPa
        fck_min_mpa=Fraction(10, 1),
        fck_max_mpa=Fraction(15, 1),  # Limite máximo de fck para condição C
        descricao=(
            "Cimento medido em massa; agregados medidos em volume; água de amassamento estimada "
            "sem controle sistemático de umidade."
        ),
    ),
}


class LimitesAgressividade(NamedTuple):
    """Exigências de durabilidade por Classe de Agressividade Ambiental (NBR 6118:2023 / NBR 12655:2022)."""
    classe: str
    agressividade: str
    classificacao_geral: str
    ac_maximo_ca: Fraction
    ac_maximo_cp: Fraction
    fck_minimo_ca: Fraction
    fck_minimo_cp: Fraction
    consumo_cimento_minimo_kg_m3: Fraction


LIMITES_CAA: dict[str, LimitesAgressividade] = {
    "CAA_I": LimitesAgressividade(
        classe="I",
        agressividade="Fraca",
        classificacao_geral="Rural ou Submersa",
        ac_maximo_ca=Fraction(13, 20),   # 0,65
        ac_maximo_cp=Fraction(3, 5),     # 0,60
        fck_minimo_ca=Fraction(20, 1),   # C20
        fck_minimo_cp=Fraction(25, 1),   # C25
        consumo_cimento_minimo_kg_m3=Fraction(260, 1),
    ),
    "CAA_II": LimitesAgressividade(
        classe="II",
        agressividade="Moderada",
        classificacao_geral="Urbana",
        ac_maximo_ca=Fraction(3, 5),     # 0,60
        ac_maximo_cp=Fraction(11, 20),   # 0,55
        fck_minimo_ca=Fraction(25, 1),   # C25
        fck_minimo_cp=Fraction(30, 1),   # C30
        consumo_cimento_minimo_kg_m3=Fraction(280, 1),
    ),
    "CAA_III": LimitesAgressividade(
        classe="III",
        agressividade="Forte",
        classificacao_geral="Marinha ou Industrial",
        ac_maximo_ca=Fraction(11, 20),   # 0,55
        ac_maximo_cp=Fraction(1, 2),     # 0,50
        fck_minimo_ca=Fraction(30, 1),   # C30
        fck_minimo_cp=Fraction(35, 1),   # C35
        consumo_cimento_minimo_kg_m3=Fraction(320, 1),
    ),
    "CAA_IV": LimitesAgressividade(
        classe="IV",
        agressividade="Muito Forte",
        classificacao_geral="Respingos de maré ou Ambientes industriais agressivos",
        ac_maximo_ca=Fraction(9, 20),    # 0,45
        ac_maximo_cp=Fraction(9, 20),    # 0,45
        fck_minimo_ca=Fraction(40, 1),   # C40
        fck_minimo_cp=Fraction(40, 1),   # C40
        consumo_cimento_minimo_kg_m3=Fraction(360, 1),
    ),
}

# Curvas de referência ABCP (28 dias) relacionando relação a/c com resistência média fcm (MPa).
# Cada curva é um conjunto ordenado de pares (a/c, fcm). Interpolação linear por trecho.
CURVAS_ABRAMS_ABCP: dict[str, list[tuple[Fraction, Fraction]]] = {
    "CP_II_32": [
        (Fraction(35, 100), Fraction(48, 1)),
        (Fraction(40, 100), Fraction(42, 1)),
        (Fraction(45, 100), Fraction(37, 1)),
        (Fraction(50, 100), Fraction(32, 1)),
        (Fraction(55, 100), Fraction(28, 1)),
        (Fraction(60, 100), Fraction(24, 1)),
        (Fraction(65, 100), Fraction(21, 1)),
        (Fraction(70, 100), Fraction(18, 1)),
        (Fraction(75, 100), Fraction(16, 1)),
    ],
    "CP_II_40": [
        (Fraction(35, 100), Fraction(56, 1)),
        (Fraction(40, 100), Fraction(50, 1)),
        (Fraction(45, 100), Fraction(44, 1)),
        (Fraction(50, 100), Fraction(39, 1)),
        (Fraction(55, 100), Fraction(34, 1)),
        (Fraction(60, 100), Fraction(30, 1)),
        (Fraction(65, 100), Fraction(26, 1)),
        (Fraction(70, 100), Fraction(23, 1)),
        (Fraction(75, 100), Fraction(20, 1)),
    ],
    "CP_III_40": [
        (Fraction(35, 100), Fraction(54, 1)),
        (Fraction(40, 100), Fraction(48, 1)),
        (Fraction(45, 100), Fraction(43, 1)),
        (Fraction(50, 100), Fraction(38, 1)),
        (Fraction(55, 100), Fraction(33, 1)),
        (Fraction(60, 100), Fraction(29, 1)),
        (Fraction(65, 100), Fraction(25, 1)),
        (Fraction(70, 100), Fraction(22, 1)),
        (Fraction(75, 100), Fraction(19, 1)),
    ],
    "CP_IV_32": [
        (Fraction(35, 100), Fraction(46, 1)),
        (Fraction(40, 100), Fraction(40, 1)),
        (Fraction(45, 100), Fraction(35, 1)),
        (Fraction(50, 100), Fraction(30, 1)),
        (Fraction(55, 100), Fraction(26, 1)),
        (Fraction(60, 100), Fraction(22, 1)),
        (Fraction(65, 100), Fraction(19, 1)),
        (Fraction(70, 100), Fraction(17, 1)),
        (Fraction(75, 100), Fraction(15, 1)),
    ],
    "CP_V_ARI": [
        (Fraction(35, 100), Fraction(62, 1)),
        (Fraction(40, 100), Fraction(55, 1)),
        (Fraction(45, 100), Fraction(48, 1)),
        (Fraction(50, 100), Fraction(42, 1)),
        (Fraction(55, 100), Fraction(37, 1)),
        (Fraction(60, 100), Fraction(32, 1)),
        (Fraction(65, 100), Fraction(28, 1)),
        (Fraction(70, 100), Fraction(24, 1)),
        (Fraction(75, 100), Fraction(21, 1)),
    ],
}

# Diâmetros nominais de agregado graúdo catalogados (mm)
DIAMETROS_MAXIMOS_VALIDOS: tuple[Fraction, ...] = (
    Fraction(19, 2),   # 9,5 mm (Brita 0)
    Fraction(25, 2),   # 12,5 mm (Brita 1/2)
    Fraction(19, 1),   # 19,0 mm (Brita 1)
    Fraction(25, 1),   # 25,0 mm (Brita 2)
    Fraction(63, 2),   # 31,5 mm (Brita 3)
    Fraction(38, 1),   # 38,0 mm (Brita 4)
)

# Slumps nominais tabelados (mm) para interpolação de consumo de água
SLUMPS_TABELADOS: tuple[int, ...] = (40, 70, 100, 135, 170)

# Tabela ABCP de consumo aproximado de água (L/m³ de concreto) sem ar incorporado
# Linha: slump nominal, Coluna: d_max (mm)
TABELA_CONSUMO_AGUA_ABCP: dict[int, dict[Fraction, Fraction]] = {
    40: {  # Faixa 30 a 50 mm
        Fraction(19, 2): Fraction(205, 1),
        Fraction(25, 2): Fraction(200, 1),
        Fraction(19, 1): Fraction(185, 1),
        Fraction(25, 1): Fraction(180, 1),
        Fraction(63, 2): Fraction(170, 1),
        Fraction(38, 1): Fraction(165, 1),
    },
    70: {  # Faixa 60 a 80 mm
        Fraction(19, 2): Fraction(220, 1),
        Fraction(25, 2): Fraction(210, 1),
        Fraction(19, 1): Fraction(200, 1),
        Fraction(25, 1): Fraction(190, 1),
        Fraction(63, 2): Fraction(180, 1),
        Fraction(38, 1): Fraction(175, 1),
    },
    100: {  # Faixa 90 a 110 mm
        Fraction(19, 2): Fraction(230, 1),
        Fraction(25, 2): Fraction(220, 1),
        Fraction(19, 1): Fraction(210, 1),
        Fraction(25, 1): Fraction(200, 1),
        Fraction(63, 2): Fraction(190, 1),
        Fraction(38, 1): Fraction(185, 1),
    },
    135: {  # Faixa 120 a 150 mm
        Fraction(19, 2): Fraction(240, 1),
        Fraction(25, 2): Fraction(230, 1),
        Fraction(19, 1): Fraction(220, 1),
        Fraction(25, 1): Fraction(210, 1),
        Fraction(63, 2): Fraction(200, 1),
        Fraction(38, 1): Fraction(195, 1),
    },
    170: {  # Faixa 160 a 180 mm
        Fraction(19, 2): Fraction(250, 1),
        Fraction(25, 2): Fraction(240, 1),
        Fraction(19, 1): Fraction(230, 1),
        Fraction(25, 1): Fraction(220, 1),
        Fraction(63, 2): Fraction(210, 1),
        Fraction(38, 1): Fraction(205, 1),
    },
}

# Volume de ar aprisionado natural (Litros por m³ de concreto) em função do d_max
TABELA_AR_APRISIONADO_LITROS: dict[Fraction, Fraction] = {
    Fraction(19, 2): Fraction(30, 1),  # 3,0%
    Fraction(25, 2): Fraction(25, 1),  # 2,5%
    Fraction(19, 1): Fraction(20, 1),  # 2,0%
    Fraction(25, 1): Fraction(15, 1),  # 1,5%
    Fraction(63, 2): Fraction(10, 1),  # 1,0%
    Fraction(38, 1): Fraction(8, 1),   # 0,8%
}

# Módulos de Finura da Areia (MF) tabelados na tabela ABCP/ACI
MODULOS_FINURA_TABELADOS: tuple[Fraction, ...] = (
    Fraction(22, 10),  # 2,20
    Fraction(24, 10),  # 2,40
    Fraction(26, 10),  # 2,60
    Fraction(28, 10),  # 2,80
    Fraction(30, 10),  # 3,00
    Fraction(32, 10),  # 3,20
)

# Tabela ABCP/ACI de Volume Compactado de Agregado Graúdo Seco (V_ob em m³ por m³ de concreto)
# em função do d_max da brita e do módulo de finura (MF) da areia.
TABELA_VOLUME_APARENTE_BRITA: dict[Fraction, dict[Fraction, Fraction]] = {
    Fraction(19, 2): {  # 9,5 mm
        Fraction(22, 10): Fraction(50, 100),
        Fraction(24, 10): Fraction(48, 100),
        Fraction(26, 10): Fraction(46, 100),
        Fraction(28, 10): Fraction(44, 100),
        Fraction(30, 10): Fraction(42, 100),
        Fraction(32, 10): Fraction(40, 100),
    },
    Fraction(25, 2): {  # 12,5 mm
        Fraction(22, 10): Fraction(59, 100),
        Fraction(24, 10): Fraction(57, 100),
        Fraction(26, 10): Fraction(55, 100),
        Fraction(28, 10): Fraction(53, 100),
        Fraction(30, 10): Fraction(51, 100),
        Fraction(32, 10): Fraction(49, 100),
    },
    Fraction(19, 1): {  # 19,0 mm
        Fraction(22, 10): Fraction(69, 100),
        Fraction(24, 10): Fraction(67, 100),
        Fraction(26, 10): Fraction(65, 100),
        Fraction(28, 10): Fraction(63, 100),
        Fraction(30, 10): Fraction(61, 100),
        Fraction(32, 10): Fraction(59, 100),
    },
    Fraction(25, 1): {  # 25,0 mm
        Fraction(22, 10): Fraction(74, 100),
        Fraction(24, 10): Fraction(72, 100),
        Fraction(26, 10): Fraction(70, 100),
        Fraction(28, 10): Fraction(68, 100),
        Fraction(30, 10): Fraction(66, 100),
        Fraction(32, 10): Fraction(64, 100),
    },
    Fraction(63, 2): {  # 31,5 mm
        Fraction(22, 10): Fraction(78, 100),
        Fraction(24, 10): Fraction(76, 100),
        Fraction(26, 10): Fraction(74, 100),
        Fraction(28, 10): Fraction(72, 100),
        Fraction(30, 10): Fraction(70, 100),
        Fraction(32, 10): Fraction(68, 100),
    },
    Fraction(38, 1): {  # 38,0 mm
        Fraction(22, 10): Fraction(81, 100),
        Fraction(24, 10): Fraction(79, 100),
        Fraction(26, 10): Fraction(77, 100),
        Fraction(28, 10): Fraction(75, 100),
        Fraction(30, 10): Fraction(73, 100),
        Fraction(32, 10): Fraction(71, 100),
    },
}
