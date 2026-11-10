"""Modelos de domínio e tipos imutáveis para dosagem de concreto ABCP.

LOFRANO TECNOLOGIA.
Todas as quantidades escalares utilizam estritamente Fraction ou int. Ponto flutuante é proibido.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Any


class CondicaoPreparo(str, Enum):
    """Condição de preparo do concreto segundo ABNT NBR 12655:2022."""
    A = "A"
    B = "B"
    C = "C"


class ClasseAgressividadeAmbiental(str, Enum):
    """Classe de Agressividade Ambiental (CAA) segundo ABNT NBR 6118 / NBR 12655."""
    CAA_I = "CAA_I"
    CAA_II = "CAA_II"
    CAA_III = "CAA_III"
    CAA_IV = "CAA_IV"


class TipoEstrutura(str, Enum):
    """Tipo estrutural para verificação de limites normativos."""
    CONCRETO_ARMADO = "CONCRETO_ARMADO"
    CONCRETO_PROTENDIDO = "CONCRETO_PROTENDIDO"


class TipoCimento(str, Enum):
    """Tipo normalizado de cimento Portland para aplicação de curvas de Abrams."""
    CP_II_32 = "CP_II_32"
    CP_II_40 = "CP_II_40"
    CP_III_40 = "CP_III_40"
    CP_IV_32 = "CP_IV_32"
    CP_V_ARI = "CP_V_ARI"
    PERSONALIZADO = "PERSONALIZADO"


@dataclass(frozen=True)
class AgregadoGraudo:
    """Propriedades físicas e ensaiadas de agregado graúdo (brita)."""
    nome: str
    d_max_mm: Fraction
    massa_unitaria_compactada_kg_m3: Fraction
    massa_especifica_real_kg_l: Fraction
    massa_unitaria_solta_kg_m3: Fraction | None = None
    umidade_pct: Fraction = Fraction(0)
    absorcao_pct: Fraction = Fraction(0)
    proporcao_mistura: Fraction = Fraction(1)


@dataclass(frozen=True)
class AgregadoMiudo:
    """Propriedades físicas e ensaiadas de agregado miúdo (areia)."""
    nome: str
    modulo_finura: Fraction
    massa_especifica_real_kg_l: Fraction
    massa_unitaria_solta_kg_m3: Fraction | None = None
    umidade_pct: Fraction = Fraction(0)
    inchamento_coeficiente: Fraction = Fraction(1)
    absorcao_pct: Fraction = Fraction(0)


@dataclass(frozen=True)
class Cimento:
    """Especificações do aglomerante e parâmetros de hidratação."""
    tipo: TipoCimento
    massa_especifica_real_kg_l: Fraction = Fraction(315, 100)  # 3,15 kg/L
    consumo_minimo_especifico_kg_m3: Fraction | None = None
    curva_abrams_personalizada: tuple[tuple[Fraction, Fraction], ...] | None = None


@dataclass(frozen=True)
class PrecosUnitarios:
    """Preços unitários de insumos em moeda nacional (R$) para orçamentação da amassada."""
    cimento_por_saco_50kg: Fraction = Fraction(0)
    areia_por_metro_cubico: Fraction = Fraction(0)
    brita_por_metro_cubico: Fraction = Fraction(0)
    agua_por_metro_cubico: Fraction = Fraction(0)
    aditivo_por_litro: Fraction = Fraction(0)


@dataclass(frozen=True)
class ParametrosDosagem:
    """Parâmetros completos de entrada para o dimensionamento do traço experimental."""
    identificacao: str
    fck_mpa: Fraction
    condicao_preparo: CondicaoPreparo
    classe_agressividade: ClasseAgressividadeAmbiental
    tipo_estrutura: TipoEstrutura
    slump_mm: int
    cimento: Cimento
    areia: AgregadoMiudo
    britas: tuple[AgregadoGraudo, ...]
    aditivo_redutor_agua_pct: Fraction = Fraction(0)
    dosagem_aditivo_pct_cimento: Fraction = Fraction(0)
    aditivo_densidade_kg_l: Fraction = Fraction(1)
    teor_ar_adicional_pct: Fraction = Fraction(0)
    precos: PrecosUnitarios = field(default_factory=PrecosUnitarios)
    volume_amassada_litros: Fraction = Fraction(1000)


@dataclass(frozen=True)
class TracoMassa:
    """Traço unitário em massa de materiais secos (1 : areia : brita : água/cimento)."""
    cimento: Fraction = Fraction(1)
    areia: Fraction = Fraction(0)
    britas: tuple[tuple[str, Fraction], ...] = ()
    brita_total: Fraction = Fraction(0)
    agua_cimento: Fraction = Fraction(0)
    soma_agregados_m: Fraction = Fraction(0)
    teor_argamassa_pct: Fraction = Fraction(0)


@dataclass(frozen=True)
class ConsumosMetroCubico:
    """Consumos em massa e volume de materiais para 1 metro cúbico (1000 Litros) de concreto."""
    cimento_kg: Fraction
    agua_litros: Fraction
    areia_kg: Fraction
    britas_kg: tuple[tuple[str, Fraction], ...]
    brita_total_kg: Fraction
    aditivo_kg: Fraction
    ar_aprisionado_litros: Fraction
    volume_cimento_litros: Fraction
    volume_agua_litros: Fraction
    volume_areia_litros: Fraction
    volumes_brita_litros: tuple[tuple[str, Fraction], ...]
    volume_brita_total_litros: Fraction
    volume_aditivo_litros: Fraction
    volume_absoluto_total_litros: Fraction
    massa_especifica_fresca_kg_m3: Fraction
    sacos_cimento_50kg: Fraction


@dataclass(frozen=True)
class AjusteCanteiro:
    """Correção operacional do traço para umidade e inchamento em canteiro de obras."""
    areia_umida_kg_m3: Fraction
    britas_umidas_kg_m3: tuple[tuple[str, Fraction], ...]
    agua_efetiva_litros_m3: Fraction
    agua_contida_agregados_litros_m3: Fraction
    traco_saco_50kg_cimento_kg: Fraction
    traco_saco_50kg_areia_umida_kg: Fraction
    traco_saco_50kg_britas_umidas_kg: tuple[tuple[str, Fraction], ...]
    traco_saco_50kg_agua_litros: Fraction
    volume_areia_padiolas_litros: Fraction | None
    volumes_brita_padiolas_litros: tuple[tuple[str, Fraction], ...] | None


@dataclass(frozen=True)
class CustoConcreto:
    """Composição de custos estimados dos materiais para a dosagem calculada."""
    custo_cimento_m3: Fraction
    custo_areia_m3: Fraction
    custo_brita_m3: Fraction
    custo_agua_m3: Fraction
    custo_aditivo_m3: Fraction
    custo_total_m3: Fraction
    custo_por_saco_cimento: Fraction


@dataclass(frozen=True)
class VerificacoesNormativas:
    """Validações de conformidade com ABNT NBR 12655:2022 e ABNT NBR 6118:2023."""
    fcm_calculado_mpa: Fraction
    desvio_padrao_adotado_mpa: Fraction
    ac_resistencia: Fraction
    ac_durabilidade_limite: Fraction
    ac_adotado: Fraction
    motivo_escolha_ac: str
    consumo_cimento_minimo_normativo: Fraction
    consumo_cimento_calculado: Fraction
    fck_minimo_normativo: Fraction
    atende_resistencia_minima: bool
    atende_consumo_minimo: bool
    atende_relacao_ac_maxima: bool
    conforme_todas_normas: bool


@dataclass(frozen=True)
class ResultadoDosagem:
    """Resultado analítico e experimental completo da dosagem de concreto ABCP."""
    parametros: ParametrosDosagem
    fck_solicitado_mpa: Fraction
    fcm_dosagem_mpa: Fraction
    slump_adotado_mm: int
    consumos_m3: ConsumosMetroCubico
    traco_seco: TracoMassa
    ajuste_canteiro: AjusteCanteiro
    custos: CustoConcreto
    verificacoes: VerificacoesNormativas
    avisos: tuple[str, ...]

    @property
    def identificacao(self) -> str:
        """Identificação do projeto/amassada."""
        return self.parametros.identificacao
