"""Codec JSON canônico e determinístico sem ponto flutuante (Zero Float).

LOFRANO TECNOLOGIA.
Rejeita floats, BOM, chaves duplicadas, valores não-finitos e profundidade excessiva (>32).
Serializa e desserializa modelos de domínio com frações exatas.
"""

from fractions import Fraction
import json
from typing import Any

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
from .errors import ErroCodecJson
from .formatters import formatar_fracao_decimal


def rejeitar_float(valor: str) -> None:
    """Interrompe decodificação com erro ao detectar qualquer número em notação de ponto flutuante."""
    raise ErroCodecJson(
        f"Ponto flutuante proibido detectado no JSON: '{valor}'. Use string com fração ou número inteiro."
    )


def verificar_chaves_duplicadas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    """Interrompe decodificação com erro se houver chaves duplicadas no objeto JSON."""
    dicionario: dict[str, Any] = {}
    for chave, valor in pares:
        if chave in dicionario:
            raise ErroCodecJson(f"Chave duplicada proibida no JSON: '{chave}'.")
        dicionario[chave] = valor
    return dicionario


def validar_profundidade(obj: Any, nivel_atual: int = 1, limite_max: int = 32) -> None:
    """Verifica e rejeita objetos com aninhamento excessivo."""
    if nivel_atual > limite_max:
        raise ErroCodecJson(
            f"Profundidade estrutural excessiva no JSON ({nivel_atual} > {limite_max})."
        )
    if isinstance(obj, dict):
        for v in obj.values():
            validar_profundidade(v, nivel_atual + 1, limite_max)
    elif isinstance(obj, list):
        for item in obj:
            validar_profundidade(item, nivel_atual + 1, limite_max)


def converter_fracao(valor: Any) -> Fraction:
    """Converte int, str ou Fraction para Fraction. Rejeita float explicitamente."""
    if isinstance(valor, float):
        raise ErroCodecJson(
            f"Ponto flutuante IEEE-754 detectado: {valor!r}. Use Fraction, int ou string decimal/fracionária."
        )
    if isinstance(valor, Fraction):
        return valor
    if isinstance(valor, int):
        return Fraction(valor, 1)
    if isinstance(valor, str):
        v = valor.strip()
        if not v:
            raise ErroCodecJson("String vazia fornecida para conversão em fração.")
        if "/" in v:
            partes = v.split("/")
            if len(partes) != 2:
                raise ErroCodecJson(f"Formato de fração inválido: '{valor}'.")
            return Fraction(int(partes[0].strip()), int(partes[1].strip()))
        # Notação decimal com vírgula ou ponto
        if "," in v:
            v = v.replace(".", "").replace(",", ".")
        if "." in v:
            partes = v.split(".")
            if len(partes) != 2:
                raise ErroCodecJson(f"Número decimal inválido: '{valor}'.")
            casas = len(partes[1])
            num = int(partes[0] + partes[1])
            den = 10**casas
            return Fraction(num, den)
        return Fraction(int(v), 1)

    raise ErroCodecJson(f"Tipo incompatível para conversão em fração: {type(valor)}.")


def serializar_fracao(f: Fraction) -> dict[str, Any]:
    """Serializa Fraction em representação canônica contendo numerador, denominador e texto decimal."""
    return {
        "numerador": f.numerator,
        "denominador": f.denominator,
        "decimal": formatar_fracao_decimal(f, casas=4),
    }


def desserializar_fracao(dado: Any) -> Fraction:
    """Recupera Fraction a partir de int, str ou dict canônico."""
    if isinstance(dado, dict) and "numerador" in dado and "denominador" in dado:
        return Fraction(int(dado["numerador"]), int(dado["denominador"]))
    return converter_fracao(dado)


def decodificar_json_seguro(texto_ou_bytes: str | bytes) -> Any:
    """Decodifica JSON com rejeição de BOM, float, chaves duplicadas e profundidade excessiva."""
    if isinstance(texto_ou_bytes, bytes):
        if texto_ou_bytes.startswith(b"\xef\xbb\xbf"):
            raise ErroCodecJson("BOM UTF-8 proibido detectado no início do arquivo JSON.")
        texto = texto_ou_bytes.decode("utf-8")
    else:
        if texto_ou_bytes.startswith("\ufeff"):
            raise ErroCodecJson("BOM UTF-8 proibido detectado no início da string JSON.")
        texto = texto_ou_bytes

    try:
        dados = json.loads(
            texto,
            parse_float=rejeitar_float,
            object_pairs_hook=verificar_chaves_duplicadas,
        )
    except json.JSONDecodeError as e:
        raise ErroCodecJson(f"Falha de sintaxe JSON: {e}") from e

    validar_profundidade(dados)
    return dados


def carregar_parametros_json(dado: dict[str, Any]) -> ParametrosDosagem:
    """Constrói instância de ParametrosDosagem a partir de dicionário decodificado."""
    try:
        identificacao = str(dado.get("identificacao", "Dosagem de Concreto ABCP"))
        fck = desserializar_fracao(dado["fck_mpa"])
        condicao = CondicaoPreparo(dado["condicao_preparo"])
        classe_agressividade = ClasseAgressividadeAmbiental(dado["classe_agressividade"])
        tipo_estrutura = TipoEstrutura(dado.get("tipo_estrutura", "CONCRETO_ARMADO"))
        slump_mm = int(dado["slump_mm"])

        # Cimento
        cim_dado = dado["cimento"]
        tipo_cim = TipoCimento(cim_dado["tipo"])
        massa_esp_cim = desserializar_fracao(cim_dado.get("massa_especifica_real_kg_l", "3.15"))
        cons_min_cim = (
            desserializar_fracao(cim_dado["consumo_minimo_especifico_kg_m3"])
            if "consumo_minimo_especifico_kg_m3" in cim_dado and cim_dado["consumo_minimo_especifico_kg_m3"] is not None
            else None
        )
        curva_custom = None
        if "curva_abrams_personalizada" in cim_dado and cim_dado["curva_abrams_personalizada"]:
            curva_custom = tuple(
                (desserializar_fracao(p[0]), desserializar_fracao(p[1]))
                for p in cim_dado["curva_abrams_personalizada"]
            )
        cimento = Cimento(
            tipo=tipo_cim,
            massa_especifica_real_kg_l=massa_esp_cim,
            consumo_minimo_especifico_kg_m3=cons_min_cim,
            curva_abrams_personalizada=curva_custom,
        )

        # Areia
        areia_dado = dado["areia"]
        areia = AgregadoMiudo(
            nome=str(areia_dado.get("nome", "Areia Média")),
            modulo_finura=desserializar_fracao(areia_dado["modulo_finura"]),
            massa_especifica_real_kg_l=desserializar_fracao(areia_dado["massa_especifica_real_kg_l"]),
            massa_unitaria_solta_kg_m3=(
                desserializar_fracao(areia_dado["massa_unitaria_solta_kg_m3"])
                if "massa_unitaria_solta_kg_m3" in areia_dado and areia_dado["massa_unitaria_solta_kg_m3"] is not None
                else None
            ),
            umidade_pct=desserializar_fracao(areia_dado.get("umidade_pct", 0)),
            inchamento_coeficiente=desserializar_fracao(areia_dado.get("inchamento_coeficiente", 1)),
            absorcao_pct=desserializar_fracao(areia_dado.get("absorcao_pct", 0)),
        )

        # Britas
        britas_lista: list[AgregadoGraudo] = []
        for b in dado["britas"]:
            britas_lista.append(
                AgregadoGraudo(
                    nome=str(b.get("nome", "Brita")),
                    d_max_mm=desserializar_fracao(b["d_max_mm"]),
                    massa_unitaria_compactada_kg_m3=desserializar_fracao(b["massa_unitaria_compactada_kg_m3"]),
                    massa_especifica_real_kg_l=desserializar_fracao(b["massa_especifica_real_kg_l"]),
                    massa_unitaria_solta_kg_m3=(
                        desserializar_fracao(b["massa_unitaria_solta_kg_m3"])
                        if "massa_unitaria_solta_kg_m3" in b and b["massa_unitaria_solta_kg_m3"] is not None
                        else None
                    ),
                    umidade_pct=desserializar_fracao(b.get("umidade_pct", 0)),
                    absorcao_pct=desserializar_fracao(b.get("absorcao_pct", 0)),
                    proporcao_mistura=desserializar_fracao(b.get("proporcao_mistura", 1)),
                )
            )

        # Aditivos e ar
        aditivo_redutor = desserializar_fracao(dado.get("aditivo_redutor_agua_pct", 0))
        dosagem_aditivo = desserializar_fracao(dado.get("dosagem_aditivo_pct_cimento", 0))
        aditivo_densidade = desserializar_fracao(dado.get("aditivo_densidade_kg_l", 1))
        teor_ar_adic = desserializar_fracao(dado.get("teor_ar_adicional_pct", 0))

        # Preços
        precos_dado = dado.get("precos", {})
        precos = PrecosUnitarios(
            cimento_por_saco_50kg=desserializar_fracao(precos_dado.get("cimento_por_saco_50kg", 0)),
            areia_por_metro_cubico=desserializar_fracao(precos_dado.get("areia_por_metro_cubico", 0)),
            brita_por_metro_cubico=desserializar_fracao(precos_dado.get("brita_por_metro_cubico", 0)),
            agua_por_metro_cubico=desserializar_fracao(precos_dado.get("agua_por_metro_cubico", 0)),
            aditivo_por_litro=desserializar_fracao(precos_dado.get("aditivo_por_litro", 0)),
        )

        return ParametrosDosagem(
            identificacao=identificacao,
            fck_mpa=fck,
            condicao_preparo=condicao,
            classe_agressividade=classe_agressividade,
            tipo_estrutura=tipo_estrutura,
            slump_mm=slump_mm,
            cimento=cimento,
            areia=areia,
            britas=tuple(britas_lista),
            aditivo_redutor_agua_pct=aditivo_redutor,
            dosagem_aditivo_pct_cimento=dosagem_aditivo,
            aditivo_densidade_kg_l=aditivo_densidade,
            teor_ar_adicional_pct=teor_ar_adic,
            precos=precos,
        )
    except KeyError as e:
        raise ErroCodecJson(f"Campo obrigatório ausente nos parâmetros de dosagem: {e}") from e
    except ValueError as e:
        raise ErroCodecJson(f"Valor inválido em campo enumerado ou numérico: {e}") from e


def resultado_para_dict(res: ResultadoDosagem) -> dict[str, Any]:
    """Converte ResultadoDosagem em estrutura serializável canônica."""
    p = res.parametros
    c = res.consumos_m3
    t = res.traco_seco
    a = res.ajuste_canteiro
    cu = res.custos
    v = res.verificacoes

    return {
        "identificacao": res.identificacao,
        "normas_referencia": [
            "ABNT NBR 12655:2022",
            "ABNT NBR 6118:2023",
            "Método ABCP/ACI",
        ],
        "solicitacao_projeto": {
            "fck_solicitado_mpa": serializar_fracao(res.fck_solicitado_mpa),
            "condicao_preparo": p.condicao_preparo.value,
            "classe_agressividade": p.classe_agressividade.value,
            "tipo_estrutura": p.tipo_estrutura.value,
            "slump_adotado_mm": res.slump_adotado_mm,
        },
        "resistencia_e_durabilidade": {
            "desvio_padrao_sd_mpa": serializar_fracao(v.desvio_padrao_adotado_mpa),
            "fcm_dosagem_mpa": serializar_fracao(res.fcm_dosagem_mpa),
            "relacao_ac_resistencia": serializar_fracao(v.ac_resistencia),
            "relacao_ac_durabilidade_limite": serializar_fracao(v.ac_durabilidade_limite),
            "relacao_ac_adotada": serializar_fracao(v.ac_adotado),
            "motivo_ac": v.motivo_escolha_ac,
            "consumo_cimento_minimo_normativo_kg_m3": serializar_fracao(v.consumo_cimento_minimo_normativo),
            "atende_resistencia_minima": v.atende_resistencia_minima,
            "atende_consumo_minimo": v.atende_consumo_minimo,
            "atende_relacao_ac_maxima": v.atende_relacao_ac_maxima,
            "conforme_todas_normas": v.conforme_todas_normas,
        },
        "traco_unitario_massa_seca": {
            "cimento": serializar_fracao(t.cimento),
            "areia": serializar_fracao(t.areia),
            "britas": [
                {"nome": b[0], "proporcao": serializar_fracao(b[1])}
                for b in t.britas
            ],
            "brita_total": serializar_fracao(t.brita_total),
            "agua_cimento": serializar_fracao(t.agua_cimento),
            "soma_agregados_m": serializar_fracao(t.soma_agregados_m),
            "teor_argamassa_pct": serializar_fracao(t.teor_argamassa_pct),
        },
        "consumos_por_metro_cubico": {
            "cimento_kg": serializar_fracao(c.cimento_kg),
            "agua_litros": serializar_fracao(c.agua_litros),
            "areia_kg": serializar_fracao(c.areia_kg),
            "britas_kg": [
                {"nome": b[0], "massa_kg": serializar_fracao(b[1])}
                for b in c.britas_kg
            ],
            "brita_total_kg": serializar_fracao(c.brita_total_kg),
            "aditivo_kg": serializar_fracao(c.aditivo_kg),
            "ar_aprisionado_litros": serializar_fracao(c.ar_aprisionado_litros),
            "volume_absoluto_total_litros": serializar_fracao(c.volume_absoluto_total_litros),
            "massa_especifica_fresca_kg_m3": serializar_fracao(c.massa_especifica_fresca_kg_m3),
            "sacos_cimento_50kg": serializar_fracao(c.sacos_cimento_50kg),
        },
        "ajuste_canteiro_obra": {
            "areia_umida_kg_m3": serializar_fracao(a.areia_umida_kg_m3),
            "britas_umidas_kg_m3": [
                {"nome": b[0], "massa_kg": serializar_fracao(b[1])}
                for b in a.britas_umidas_kg_m3
            ],
            "agua_contida_agregados_litros_m3": serializar_fracao(a.agua_contida_agregados_litros_m3),
            "agua_efetiva_adicionar_litros_m3": serializar_fracao(a.agua_efetiva_litros_m3),
            "proporcao_por_saco_50kg": {
                "cimento_kg": serializar_fracao(a.traco_saco_50kg_cimento_kg),
                "areia_umida_kg": serializar_fracao(a.traco_saco_50kg_areia_umida_kg),
                "britas_umidas_kg": [
                    {"nome": b[0], "massa_kg": serializar_fracao(b[1])}
                    for b in a.traco_saco_50kg_britas_umidas_kg
                ],
                "agua_adicionar_litros": serializar_fracao(a.traco_saco_50kg_agua_litros),
                "padiola_areia_litros": (
                    serializar_fracao(a.volume_areia_padiolas_litros)
                    if a.volume_areia_padiolas_litros is not None
                    else None
                ),
                "padiolas_brita_litros": (
                    [{"nome": b[0], "volume_litros": serializar_fracao(b[1])} for b in a.volumes_brita_padiolas_litros]
                    if a.volumes_brita_padiolas_litros is not None
                    else None
                ),
            },
        },
        "custos_materiais": {
            "custo_cimento_m3": serializar_fracao(cu.custo_cimento_m3),
            "custo_areia_m3": serializar_fracao(cu.custo_areia_m3),
            "custo_brita_m3": serializar_fracao(cu.custo_brita_m3),
            "custo_agua_m3": serializar_fracao(cu.custo_agua_m3),
            "custo_aditivo_m3": serializar_fracao(cu.custo_aditivo_m3),
            "custo_total_m3": serializar_fracao(cu.custo_total_m3),
            "custo_por_saco_cimento": serializar_fracao(cu.custo_por_saco_cimento),
        },
        "avisos": list(res.avisos),
    }


def serializar_json_canonico(objeto: Any) -> str:
    """Serializa dados em formato JSON canônico, determinístico, ordenado e indentado."""
    return json.dumps(
        objeto,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
