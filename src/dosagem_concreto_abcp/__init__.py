"""dosagem-concreto-abcp — Dosagem Experimental e Analítica de Concreto pelo Método ABCP/ACI.

LOFRANO TECNOLOGIA.
Normas de referência: ABNT NBR 12655:2022 e ABNT NBR 6118:2023.
Aritmética 100% racional e inteira sem ponto flutuante (Zero Float).
Zero dependências externas de runtime.
"""

from .calculator import (
    calcular_ajuste_canteiro,
    calcular_consumo_agua,
    calcular_custos,
    calcular_dosagem_abcp,
    calcular_fcm,
    calcular_relacao_ac_resistencia,
    calcular_volume_aparente_brita,
    obter_desvio_padrao,
    obter_limites_caa,
    validar_parametros,
)
from .constants import (
    FATOR_QUANTIL_NORMAL,
    LIMITES_CAA,
    REGRAS_CONDICAO_PREPARO,
    TABELA_CONSUMO_AGUA_ABCP,
    TABELA_VOLUME_APARENTE_BRITA,
)
from .domain import (
    AgregadoGraudo,
    AgregadoMiudo,
    AjusteCanteiro,
    Cimento,
    ClasseAgressividadeAmbiental,
    CondicaoPreparo,
    ConsumosMetroCubico,
    CustoConcreto,
    ParametrosDosagem,
    PrecosUnitarios,
    ResultadoDosagem,
    TipoCimento,
    TipoEstrutura,
    TracoMassa,
    VerificacoesNormativas,
)
from .errors import (
    ErroAgregadoInvalido,
    ErroClasseAgressividade,
    ErroCodecJson,
    ErroCondicaoPreparoIncompativel,
    ErroConsumoCimentoInvalido,
    ErroDosagemConcreto,
    ErroExportacao,
    ErroResistenciaInvalida,
    ErroSlumpInvalido,
    ErroValidacaoParametros,
)
from .exports import gerar_csv, gerar_markdown, gerar_painel_svg
from .formatters import (
    formatar_fracao_decimal,
    formatar_moeda,
    formatar_traco_saco_50kg,
    formatar_traco_unitario,
)
from .json_codec import (
    carregar_parametros_json,
    decodificar_json_seguro,
    resultado_para_dict,
    serializar_json_canonico,
)
from .packaging import salvar_zip_deterministico

__version__ = "1.0.0"
__author__ = "Martin Lofrano de Oliveira (Lofrano Tecnologia)"

__all__ = [
    "__version__",
    "calcular_dosagem_abcp",
    "validar_parametros",
    "calcular_fcm",
    "calcular_relacao_ac_resistencia",
    "calcular_consumo_agua",
    "calcular_volume_aparente_brita",
    "calcular_ajuste_canteiro",
    "calcular_custos",
    "obter_desvio_padrao",
    "obter_limites_caa",
    "ParametrosDosagem",
    "ResultadoDosagem",
    "ConsumosMetroCubico",
    "TracoMassa",
    "AjusteCanteiro",
    "CustoConcreto",
    "VerificacoesNormativas",
    "AgregadoGraudo",
    "AgregadoMiudo",
    "Cimento",
    "PrecosUnitarios",
    "CondicaoPreparo",
    "ClasseAgressividadeAmbiental",
    "TipoEstrutura",
    "TipoCimento",
    "ErroDosagemConcreto",
    "ErroValidacaoParametros",
    "ErroResistenciaInvalida",
    "ErroCondicaoPreparoIncompativel",
    "ErroClasseAgressividade",
    "ErroAgregadoInvalido",
    "ErroSlumpInvalido",
    "ErroConsumoCimentoInvalido",
    "ErroCodecJson",
    "ErroExportacao",
    "formatar_fracao_decimal",
    "formatar_moeda",
    "formatar_traco_unitario",
    "formatar_traco_saco_50kg",
    "decodificar_json_seguro",
    "carregar_parametros_json",
    "resultado_para_dict",
    "serializar_json_canonico",
    "gerar_markdown",
    "gerar_csv",
    "gerar_painel_svg",
    "salvar_zip_deterministico",
    "REGRAS_CONDICAO_PREPARO",
    "LIMITES_CAA",
    "TABELA_CONSUMO_AGUA_ABCP",
    "TABELA_VOLUME_APARENTE_BRITA",
    "FATOR_QUANTIL_NORMAL",
]
