"""Exceções especializadas para o motor de dosagem de concreto ABCP.

LOFRANO TECNOLOGIA.
"""

from typing import Any


class ErroDosagemConcreto(Exception):
    """Exceção base para todas as falhas de dosagem de concreto."""


class ErroValidacaoParametros(ErroDosagemConcreto):
    """Lançada quando parâmetros de entrada são inválidos ou violam limites físicos/normativos."""


class ErroResistenciaInvalida(ErroValidacaoParametros):
    """Lançada quando fck está fora dos limites normativos (ex: < 10 MPa ou > 100 MPa)."""


class ErroCondicaoPreparoIncompativel(ErroValidacaoParametros):
    """Lançada quando a condição de preparo (A, B ou C) é incompatível com o fck exigido segundo a NBR 12655."""


class ErroClasseAgressividade(ErroValidacaoParametros):
    """Lançada quando a Classe de Agressividade Ambiental (CAA) ou restrições de durabilidade são violadas."""


class ErroAgregadoInvalido(ErroValidacaoParametros):
    """Lançada quando propriedades dos agregados miúdos ou graúdos são inconsistentes."""


class ErroSlumpInvalido(ErroValidacaoParametros):
    """Lançada quando o abatimento do tronco de cone (slump) está fora das faixas catalogadas."""


class ErroConsumoCimentoInvalido(ErroDosagemConcreto):
    """Lançada quando o consumo de cimento calculado não atinge o mínimo normativo ou excede a viabilidade técnica."""


class ErroCodecJson(ErroDosagemConcreto):
    """Lançada durante decodificação ou validação de arquivo JSON."""


class ErroExportacao(ErroDosagemConcreto):
    """Lançada em falhas de geração de relatórios, planilhas ou pacotes ZIP."""
