"""Motor de cálculo analítico e experimental de dosagem pelo Método ABCP/ACI.

LOFRANO TECNOLOGIA.
Todas as computações são conduzidas estritamente com frações exatas (Fraction) e inteiros.
Zero uso de ponto flutuante (float).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .constants import (
    CURVAS_ABRAMS_ABCP,
    DIAMETROS_MAXIMOS_VALIDOS,
    FATOR_QUANTIL_NORMAL,
    LIMITES_CAA,
    LimitesAgressividade,
    MODULOS_FINURA_TABELADOS,
    REGRAS_CONDICAO_PREPARO,
    SLUMPS_TABELADOS,
    TABELA_AR_APRISIONADO_LITROS,
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
    ErroCondicaoPreparoIncompativel,
    ErroConsumoCimentoInvalido,
    ErroResistenciaInvalida,
    ErroSlumpInvalido,
    ErroValidacaoParametros,
)


def validar_parametros(params: ParametrosDosagem) -> None:
    """Valida limites físicos e normativos dos parâmetros de dosagem."""
    if params.fck_mpa < Fraction(10, 1):
        raise ErroResistenciaInvalida(
            f"fck ({params.fck_mpa} MPa) é inferior ao limite mínimo normativo de 10 MPa (ABNT NBR 12655)."
        )
    if params.fck_mpa > Fraction(100, 1):
        raise ErroResistenciaInvalida(
            f"fck ({params.fck_mpa} MPa) excede o limite prático de 100 MPa para dosagem convencional ABCP."
        )

    # Validar condição de preparo
    regra_condicao = REGRAS_CONDICAO_PREPARO[params.condicao_preparo.value]
    if regra_condicao.fck_max_mpa is not None and params.fck_mpa > regra_condicao.fck_max_mpa:
        raise ErroCondicaoPreparoIncompativel(
            f"A {regra_condicao.nome} só é permitida para fck <= {regra_condicao.fck_max_mpa} MPa "
            f"(solicitado: {params.fck_mpa} MPa) segundo a ABNT NBR 12655:2022."
        )

    # Validar slump
    if params.slump_mm < 30 or params.slump_mm > 180:
        raise ErroSlumpInvalido(
            f"Abatimento do tronco de cone (slump = {params.slump_mm} mm) fora da faixa operacional [30, 180] mm."
        )

    # Validar agregados graúdos
    if not params.britas:
        raise ErroAgregadoInvalido("Pelo menos um agregado graúdo (brita) deve ser especificado.")

    soma_proporcoes = sum(b.proporcao_mistura for b in params.britas)
    if soma_proporcoes <= Fraction(0):
        raise ErroAgregadoInvalido("A soma das proporções da mistura de britas deve ser positiva.")

    for b in params.britas:
        if b.d_max_mm <= Fraction(0):
            raise ErroAgregadoInvalido(f"d_max da brita '{b.nome}' deve ser positivo.")
        if b.massa_unitaria_compactada_kg_m3 <= Fraction(0):
            raise ErroAgregadoInvalido(f"Massa unitária compactada da brita '{b.nome}' deve ser positiva.")
        if b.massa_especifica_real_kg_l <= Fraction(0):
            raise ErroAgregadoInvalido(f"Massa específica real da brita '{b.nome}' deve ser positiva.")

    # Validar areia
    if params.areia.modulo_finura < Fraction(18, 10) or params.areia.modulo_finura > Fraction(36, 10):
        raise ErroAgregadoInvalido(
            f"Módulo de finura da areia ({params.areia.modulo_finura}) fora dos limites válidos [1.80, 3.60]."
        )
    if params.areia.massa_especifica_real_kg_l <= Fraction(0):
        raise ErroAgregadoInvalido("Massa específica real da areia deve ser positiva.")

    # Validar cimento
    if params.cimento.massa_especifica_real_kg_l <= Fraction(0):
        raise ErroValidacaoParametros("Massa específica real do cimento deve ser positiva.")


def obter_desvio_padrao(condicao: CondicaoPreparo) -> Fraction:
    """Retorna o desvio-padrão de dosagem sd em MPa conforme NBR 12655."""
    return REGRAS_CONDICAO_PREPARO[condicao.value].desvio_padrao_mpa


def calcular_fcm(fck: Fraction, condicao: CondicaoPreparo) -> Fraction:
    """Calcula a resistência média de dosagem fcm = fck + 1,65 * sd em MPa."""
    sd = obter_desvio_padrao(condicao)
    return fck + FATOR_QUANTIL_NORMAL * sd


def interpolar_linear_racional(
    x: Fraction,
    x0: Fraction,
    y0: Fraction,
    x1: Fraction,
    y1: Fraction,
) -> Fraction:
    """Interpolação linear exata racional entre dois pontos (x0, y0) e (x1, y1)."""
    if x1 == x0:
        return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def calcular_relacao_ac_resistencia(
    fcm: Fraction,
    tipo_cimento: TipoCimento,
    curva_personalizada: Sequence[tuple[Fraction, Fraction]] | None = None,
) -> Fraction:
    """Determina a relação água/cimento (a/c) necessária para atingir fcm via curva de Abrams."""
    if tipo_cimento == TipoCimento.PERSONALIZADO:
        if not curva_personalizada or len(curva_personalizada) < 2:
            raise ErroValidacaoParametros(
                "Curva de Abrams personalizada exige ao menos dois pontos (a/c, fcm)."
            )
        pontos = sorted(curva_personalizada, key=lambda p: p[0])
    else:
        pontos = CURVAS_ABRAMS_ABCP[tipo_cimento.value]

    # Pontos estão ordenados por a/c crescente, com fcm decrescente
    # fcm_max no menor a/c, fcm_min no maior a/c
    menor_ac, maior_fcm = pontos[0]
    maior_ac, menor_fcm = pontos[-1]

    if fcm >= maior_fcm:
        # Se fcm exigido é superior ao ponto máximo tabelado, extrapola linearmente pelo primeiro trecho
        p0, p1 = pontos[0], pontos[1]
        ac = interpolar_linear_racional(fcm, p0[1], p0[0], p1[1], p1[0])
        return max(Fraction(25, 100), ac)  # limite físico inferior prático a/c 0,25

    if fcm <= menor_fcm:
        # Se fcm exigido é inferior ao ponto mínimo tabelado, extrapola linearmente pelo último trecho
        p0, p1 = pontos[-2], pontos[-1]
        ac = interpolar_linear_racional(fcm, p0[1], p0[0], p1[1], p1[0])
        return min(Fraction(85, 100), ac)  # limite superior prático a/c 0,85

    # Encontrar intervalo de fcm
    for i in range(len(pontos) - 1):
        ac_a, f_a = pontos[i]
        ac_b, f_b = pontos[i + 1]
        if f_b <= fcm <= f_a:
            # fcm está entre f_a (maior) e f_b (menor)
            return interpolar_linear_racional(fcm, f_a, ac_a, f_b, ac_b)

    return pontos[-1][0]


def obter_limites_caa(
    caa: ClasseAgressividadeAmbiental,
    tipo_estrutura: TipoEstrutura,
) -> LimitesAgressividade:
    """Retorna os limites de durabilidade para a Classe de Agressividade Ambiental."""
    return LIMITES_CAA[caa.value]


def calcular_consumo_agua(
    slump_mm: int,
    d_max_mm: Fraction,
    aditivo_redutor_agua_pct: Fraction = Fraction(0),
) -> tuple[Fraction, Fraction]:
    """Calcula o consumo de água de amassamento (L/m³) e o ar aprisionado (L/m³).

    Retorna tupla: (consumo_agua_litros, ar_aprisionado_litros).
    """
    # 1. Encontrar diâmetros limítrofes para interpolação
    d_list = sorted(DIAMETROS_MAXIMOS_VALIDOS)
    if d_max_mm <= d_list[0]:
        d0 = d1 = d_list[0]
    elif d_max_mm >= d_list[-1]:
        d0 = d1 = d_list[-1]
    else:
        for i in range(len(d_list) - 1):
            if d_list[i] <= d_max_mm <= d_list[i + 1]:
                d0, d1 = d_list[i], d_list[i + 1]
                break
        else:
            d0 = d1 = d_list[0]

    # 2. Interpolar ar aprisionado
    ar0 = TABELA_AR_APRISIONADO_LITROS[d0]
    ar1 = TABELA_AR_APRISIONADO_LITROS[d1]
    ar_litros = interpolar_linear_racional(d_max_mm, d0, ar0, d1, ar1)

    # 3. Interpolar água por slump
    slump_list = sorted(SLUMPS_TABELADOS)
    if slump_mm <= slump_list[0]:
        s0 = s1 = slump_list[0]
    elif slump_mm >= slump_list[-1]:
        s0 = s1 = slump_list[-1]
    else:
        for i in range(len(slump_list) - 1):
            if slump_list[i] <= slump_mm <= slump_list[i + 1]:
                s0, s1 = slump_list[i], slump_list[i + 1]
                break
        else:
            s0 = s1 = slump_list[0]

    # Água em s0 para d_max
    agua_s0_d0 = TABELA_CONSUMO_AGUA_ABCP[s0][d0]
    agua_s0_d1 = TABELA_CONSUMO_AGUA_ABCP[s0][d1]
    agua_s0 = interpolar_linear_racional(d_max_mm, d0, agua_s0_d0, d1, agua_s0_d1)

    # Água em s1 para d_max
    agua_s1_d0 = TABELA_CONSUMO_AGUA_ABCP[s1][d0]
    agua_s1_d1 = TABELA_CONSUMO_AGUA_ABCP[s1][d1]
    agua_s1 = interpolar_linear_racional(d_max_mm, d0, agua_s1_d0, d1, agua_s1_d1)

    # Água interpolada pelo slump
    agua_base = interpolar_linear_racional(
        Fraction(slump_mm, 1),
        Fraction(s0, 1),
        agua_s0,
        Fraction(s1, 1),
        agua_s1,
    )

    # Redução por aditivo plastificante/superplastificante
    if aditivo_redutor_agua_pct > Fraction(0):
        fator_reducao = Fraction(1, 1) - (aditivo_redutor_agua_pct / Fraction(100, 1))
        agua_final = agua_base * fator_reducao
    else:
        agua_final = agua_base

    return agua_final, ar_litros


def calcular_volume_aparente_brita(
    d_max_mm: Fraction,
    modulo_finura: Fraction,
) -> Fraction:
    """Interpolação bilinear racional do volume aparente de brita compactada seca V_ob (m³/m³)."""
    # Limitar e encontrar diâmetros vizinhos
    d_list = sorted(DIAMETROS_MAXIMOS_VALIDOS)
    if d_max_mm <= d_list[0]:
        d0 = d1 = d_list[0]
    elif d_max_mm >= d_list[-1]:
        d0 = d1 = d_list[-1]
    else:
        for i in range(len(d_list) - 1):
            if d_list[i] <= d_max_mm <= d_list[i + 1]:
                d0, d1 = d_list[i], d_list[i + 1]
                break
        else:
            d0 = d1 = d_list[0]

    # Limitar e encontrar módulos de finura vizinhos
    mf_list = sorted(MODULOS_FINURA_TABELADOS)
    if modulo_finura <= mf_list[0]:
        mf0 = mf1 = mf_list[0]
    elif modulo_finura >= mf_list[-1]:
        mf0 = mf1 = mf_list[-1]
    else:
        for i in range(len(mf_list) - 1):
            if mf_list[i] <= modulo_finura <= mf_list[i + 1]:
                mf0, mf1 = mf_list[i], mf_list[i + 1]
                break
        else:
            mf0 = mf1 = mf_list[0]

    # V_ob nos quatro cantos da malha
    v00 = TABELA_VOLUME_APARENTE_BRITA[d0][mf0]
    v01 = TABELA_VOLUME_APARENTE_BRITA[d0][mf1]
    v10 = TABELA_VOLUME_APARENTE_BRITA[d1][mf0]
    v11 = TABELA_VOLUME_APARENTE_BRITA[d1][mf1]

    # Interpolação no diâmetro d0 e d1
    v_d0 = interpolar_linear_racional(modulo_finura, mf0, v00, mf1, v01)
    v_d1 = interpolar_linear_racional(modulo_finura, mf0, v10, mf1, v11)

    # Interpolação final no diâmetro d_max
    return interpolar_linear_racional(d_max_mm, d0, v_d0, d1, v_d1)


def calcular_custos(
    consumos: ConsumosMetroCubico,
    precos: PrecosUnitarios,
    massa_unitaria_solta_areia: Fraction | None = None,
    massa_unitaria_solta_brita: Fraction | None = None,
) -> CustoConcreto:
    """Calcula a estimativa de custos de insumos por m³ de concreto e por saco de cimento."""
    # Cimento (preço informado por saco de 50 kg)
    if precos.cimento_por_saco_50kg > Fraction(0):
        preco_kg_cimento = precos.cimento_por_saco_50kg / Fraction(50, 1)
        custo_cimento = consumos.cimento_kg * preco_kg_cimento
    else:
        custo_cimento = Fraction(0)

    # Areia (preço informado por metro cúbico)
    if precos.areia_por_metro_cubico > Fraction(0):
        densidade_comercial = massa_unitaria_solta_areia or Fraction(1400, 1)
        volume_areia_m3 = consumos.areia_kg / densidade_comercial
        custo_areia = volume_areia_m3 * precos.areia_por_metro_cubico
    else:
        custo_areia = Fraction(0)

    # Brita (preço informado por metro cúbico)
    if precos.brita_por_metro_cubico > Fraction(0):
        densidade_comercial = massa_unitaria_solta_brita or Fraction(1450, 1)
        volume_brita_m3 = consumos.brita_total_kg / densidade_comercial
        custo_brita = volume_brita_m3 * precos.brita_por_metro_cubico
    else:
        custo_brita = Fraction(0)

    # Água (preço por m³ = 1000 Litros)
    if precos.agua_por_metro_cubico > Fraction(0):
        custo_agua = (consumos.agua_litros / Fraction(1000, 1)) * precos.agua_por_metro_cubico
    else:
        custo_agua = Fraction(0)

    # Aditivo (preço por Litro)
    if precos.aditivo_por_litro > Fraction(0):
        custo_aditivo = consumos.volume_aditivo_litros * precos.aditivo_por_litro
    else:
        custo_aditivo = Fraction(0)

    custo_total = custo_cimento + custo_areia + custo_brita + custo_agua + custo_aditivo

    if consumos.cimento_kg > Fraction(0):
        custo_por_saco = custo_total * (Fraction(50, 1) / consumos.cimento_kg)
    else:
        custo_por_saco = Fraction(0)

    return CustoConcreto(
        custo_cimento_m3=custo_cimento,
        custo_areia_m3=custo_areia,
        custo_brita_m3=custo_brita,
        custo_agua_m3=custo_agua,
        custo_aditivo_m3=custo_aditivo,
        custo_total_m3=custo_total,
        custo_por_saco_cimento=custo_por_saco,
    )


def calcular_ajuste_canteiro(
    consumos: ConsumosMetroCubico,
    areia: AgregadoMiudo,
    britas: Sequence[AgregadoGraudo],
) -> AjusteCanteiro:
    """Calcula correções de umidade e proporções de canteiro por saco de cimento de 50 kg."""
    # Areia úmida: massa_seca * (1 + h)
    fator_umidade_areia = Fraction(1, 1) + (areia.umidade_pct / Fraction(100, 1))
    areia_umida_kg_m3 = consumos.areia_kg * fator_umidade_areia
    agua_areia = consumos.areia_kg * (areia.umidade_pct / Fraction(100, 1))

    # Britas úmidas
    britas_umidas: list[tuple[str, Fraction]] = []
    agua_britas = Fraction(0)
    for b, (_, massa_seca) in zip(britas, consumos.britas_kg):
        fator_u_b = Fraction(1, 1) + (b.umidade_pct / Fraction(100, 1))
        massa_u = massa_seca * fator_u_b
        britas_umidas.append((b.nome, massa_u))
        agua_britas += massa_seca * (b.umidade_pct / Fraction(100, 1))

    agua_contida_agregados = agua_areia + agua_britas
    agua_efetiva_m3 = max(Fraction(0), consumos.agua_litros - agua_contida_agregados)

    # Proporções por saco de cimento de 50 kg
    fator_saco = Fraction(50, 1) / consumos.cimento_kg
    saco_cimento_kg = Fraction(50, 1)
    saco_areia_umida_kg = areia_umida_kg_m3 * fator_saco
    saco_britas_umidas = tuple((nome, m * fator_saco) for nome, m in britas_umidas)
    saco_agua_litros = agua_efetiva_m3 * fator_saco

    # Padiolas em volume (Litros por saco)
    if areia.massa_unitaria_solta_kg_m3 and areia.massa_unitaria_solta_kg_m3 > Fraction(0):
        # Inchamento: se a areia está úmida, seu volume solto aumenta pelo fator de inchamento
        inchamento = areia.inchamento_coeficiente if areia.inchamento_coeficiente >= Fraction(1, 1) else Fraction(1, 1)
        vol_areia_padiola = (saco_areia_umida_kg / areia.massa_unitaria_solta_kg_m3) * Fraction(1000, 1) * inchamento
    else:
        vol_areia_padiola = None

    vols_brita_padiolas: list[tuple[str, Fraction]] = []
    tem_vol_brita = True
    for b, (_, massa_saco) in zip(britas, saco_britas_umidas):
        if b.massa_unitaria_solta_kg_m3 and b.massa_unitaria_solta_kg_m3 > Fraction(0):
            vol_b = (massa_saco / b.massa_unitaria_solta_kg_m3) * Fraction(1000, 1)
            vols_brita_padiolas.append((b.nome, vol_b))
        else:
            tem_vol_brita = False
            break

    return AjusteCanteiro(
        areia_umida_kg_m3=areia_umida_kg_m3,
        britas_umidas_kg_m3=tuple(britas_umidas),
        agua_efetiva_litros_m3=agua_efetiva_m3,
        agua_contida_agregados_litros_m3=agua_contida_agregados,
        traco_saco_50kg_cimento_kg=saco_cimento_kg,
        traco_saco_50kg_areia_umida_kg=saco_areia_umida_kg,
        traco_saco_50kg_britas_umidas_kg=saco_britas_umidas,
        traco_saco_50kg_agua_litros=saco_agua_litros,
        volume_areia_padiolas_litros=vol_areia_padiola,
        volumes_brita_padiolas_litros=tuple(vols_brita_padiolas) if tem_vol_brita else None,
    )


def calcular_dosagem_abcp(params: ParametrosDosagem) -> ResultadoDosagem:
    """Executa a dosagem completa pelo Método ABCP/ACI com garantias da NBR 12655 e NBR 6118."""
    validar_parametros(params)
    avisos: list[str] = []

    # 1. Resistência média de dosagem fcm
    fcm = calcular_fcm(params.fck_mpa, params.condicao_preparo)
    sd = obter_desvio_padrao(params.condicao_preparo)

    # 2. Relação água/cimento por resistência mecânica
    ac_resistencia = calcular_relacao_ac_resistencia(
        fcm,
        params.cimento.tipo,
        params.cimento.curva_abrams_personalizada,
    )

    # 3. Limites de durabilidade por agressividade ambiental (CAA)
    limites_caa = obter_limites_caa(params.classe_agressividade, params.tipo_estrutura)
    ac_max_durabilidade = (
        limites_caa.ac_maximo_cp
        if params.tipo_estrutura == TipoEstrutura.CONCRETO_PROTENDIDO
        else limites_caa.ac_maximo_ca
    )
    fck_min_durabilidade = (
        limites_caa.fck_minimo_cp
        if params.tipo_estrutura == TipoEstrutura.CONCRETO_PROTENDIDO
        else limites_caa.fck_minimo_ca
    )

    # Verificação de conformidade do fck solicitado com a CAA
    atende_resistencia_minima = params.fck_mpa >= fck_min_durabilidade
    if not atende_resistencia_minima:
        avisos.append(
            f"fck solicitado ({params.fck_mpa} MPa) é inferior ao mínimo normativo de {fck_min_durabilidade} MPa "
            f"para {limites_caa.classe} ({limites_caa.agressividade}). Recomenda-se elevar o fck de projeto."
        )

    # 4. Seleção da relação a/c adotada
    if ac_resistencia <= ac_max_durabilidade:
        ac_adotado = ac_resistencia
        motivo_ac = "Condicionada pela resistência mecânica de dosagem (fcm)."
    else:
        ac_adotado = ac_max_durabilidade
        motivo_ac = (
            f"Limitada pela Classe de Agressividade Ambiental {limites_caa.classe} "
            f"(máx a/c = {ac_max_durabilidade})."
        )
        avisos.append(
            f"A relação a/c de dosagem foi reduzida de {ac_resistencia} para {ac_max_durabilidade} "
            f"por exigência de durabilidade da NBR 6118/12655."
        )

    # 5. Consumo de água de amassamento e ar aprisionado
    # Determinar d_max ponderado ou maior d_max da mistura
    d_max_composto = max(b.d_max_mm for b in params.britas)
    agua_consumo, ar_litros_natural = calcular_consumo_agua(
        params.slump_mm,
        d_max_composto,
        params.aditivo_redutor_agua_pct,
    )
    ar_total_litros = ar_litros_natural + (params.teor_ar_adicional_pct * Fraction(10, 1))

    # 6. Consumo de cimento (kg/m³)
    consumo_cimento_calculado = agua_consumo / ac_adotado

    # Mínimo de cimento normativo
    consumo_cimento_minimo_normativo = limites_caa.consumo_cimento_minimo_kg_m3
    if params.cimento.consumo_minimo_especifico_kg_m3:
        consumo_cimento_minimo_normativo = max(
            consumo_cimento_minimo_normativo,
            params.cimento.consumo_minimo_especifico_kg_m3,
        )

    if consumo_cimento_calculado < consumo_cimento_minimo_normativo:
        consumo_cimento_adotado = consumo_cimento_minimo_normativo
        ac_efetivo = agua_consumo / consumo_cimento_adotado
        avisos.append(
            f"Consumo de cimento foi elevado de {consumo_cimento_calculado} kg/m³ para o mínimo normativo de "
            f"{consumo_cimento_minimo_normativo} kg/m³ (a/c efetivo reduzido para {ac_efetivo})."
        )
    else:
        consumo_cimento_adotado = consumo_cimento_calculado
        ac_efetivo = ac_adotado

    # 7. Aditivo plastificante / químico
    if params.dosagem_aditivo_pct_cimento > Fraction(0):
        aditivo_kg = consumo_cimento_adotado * (params.dosagem_aditivo_pct_cimento / Fraction(100, 1))
        densidade_aditivo = (
            params.aditivo_densidade_kg_l
            if params.aditivo_densidade_kg_l > Fraction(0)
            else Fraction(1, 1)
        )
        volume_aditivo_litros = aditivo_kg / densidade_aditivo
    else:
        aditivo_kg = Fraction(0)
        volume_aditivo_litros = Fraction(0)

    # 8. Consumo de Agregado Graúdo (Brita) pelo método ABCP
    soma_proporcoes_brita = sum(b.proporcao_mistura for b in params.britas)
    britas_kg_lista: list[tuple[str, Fraction]] = []
    volumes_brita_lista: list[tuple[str, Fraction]] = []
    brita_total_kg = Fraction(0)
    volume_brita_total_litros = Fraction(0)

    for b in params.britas:
        prop = b.proporcao_mistura / soma_proporcoes_brita
        # V_ob específico para o d_max da brita
        v_ob = calcular_volume_aparente_brita(b.d_max_mm, params.areia.modulo_finura)
        massa_brita_i = v_ob * prop * b.massa_unitaria_compactada_kg_m3
        vol_brita_i = massa_brita_i / b.massa_especifica_real_kg_l

        britas_kg_lista.append((b.nome, massa_brita_i))
        volumes_brita_lista.append((b.nome, vol_brita_i))
        brita_total_kg += massa_brita_i
        volume_brita_total_litros += vol_brita_i

    # 9. Volume de Cimento e Água
    volume_cimento_litros = consumo_cimento_adotado / params.cimento.massa_especifica_real_kg_l
    volume_agua_litros = agua_consumo  # densidade da água = 1,00 kg/L

    # 10. Balanço do Volume Absoluto (1000 Litros) para determinar a Areia
    volume_demais_materiais = (
        volume_cimento_litros
        + volume_agua_litros
        + volume_brita_total_litros
        + ar_total_litros
        + volume_aditivo_litros
    )

    volume_areia_litros = Fraction(1000, 1) - volume_demais_materiais
    if volume_areia_litros <= Fraction(0):
        raise ErroConsumoCimentoInvalido(
            f"O volume absoluto dos demais componentes ({volume_demais_materiais} L) esgotou o volume unitário de 1000 L. "
            f"Reduza o teor de brita ou o consumo de pasta."
        )

    areia_kg = volume_areia_litros * params.areia.massa_especifica_real_kg_l

    # Volume absoluto total deve fechar exatamente em 1000 L
    volume_absoluto_total = volume_demais_materiais + volume_areia_litros

    # Massa específica aparente do concreto fresco (kg/m³)
    massa_fresca = consumo_cimento_adotado + agua_consumo + areia_kg + brita_total_kg + aditivo_kg
    sacos_cimento = consumo_cimento_adotado / Fraction(50, 1)

    consumos_m3 = ConsumosMetroCubico(
        cimento_kg=consumo_cimento_adotado,
        agua_litros=agua_consumo,
        areia_kg=areia_kg,
        britas_kg=tuple(britas_kg_lista),
        brita_total_kg=brita_total_kg,
        aditivo_kg=aditivo_kg,
        ar_aprisionado_litros=ar_total_litros,
        volume_cimento_litros=volume_cimento_litros,
        volume_agua_litros=volume_agua_litros,
        volume_areia_litros=volume_areia_litros,
        volumes_brita_litros=tuple(volumes_brita_lista),
        volume_brita_total_litros=volume_brita_total_litros,
        volume_aditivo_litros=volume_aditivo_litros,
        volume_absoluto_total_litros=volume_absoluto_total,
        massa_especifica_fresca_kg_m3=massa_fresca,
        sacos_cimento_50kg=sacos_cimento,
    )

    # 11. Traço Unitário em Massa Seca: 1 : m_a : m_b : a/c
    m_areia = areia_kg / consumo_cimento_adotado
    britas_traco = tuple(
        (nome, massa / consumo_cimento_adotado) for nome, massa in britas_kg_lista
    )
    m_brita_total = brita_total_kg / consumo_cimento_adotado
    soma_agregados_m = m_areia + m_brita_total
    teor_argamassa_pct = (
        (Fraction(1, 1) + m_areia) / (Fraction(1, 1) + soma_agregados_m)
    ) * Fraction(100, 1)

    traco_seco = TracoMassa(
        cimento=Fraction(1, 1),
        areia=m_areia,
        britas=britas_traco,
        brita_total=m_brita_total,
        agua_cimento=ac_efetivo,
        soma_agregados_m=soma_agregados_m,
        teor_argamassa_pct=teor_argamassa_pct,
    )

    # 12. Ajuste de canteiro / umidade
    ajuste_canteiro = calcular_ajuste_canteiro(consumos_m3, params.areia, params.britas)

    # 13. Custos de materiais
    custos = calcular_custos(
        consumos_m3,
        params.precos,
        massa_unitaria_solta_areia=params.areia.massa_unitaria_solta_kg_m3,
        massa_unitaria_solta_brita=(
            params.britas[0].massa_unitaria_solta_kg_m3 if params.britas else None
        ),
    )

    # 14. Verificações Normativas
    atende_consumo_minimo = consumo_cimento_adotado >= consumo_cimento_minimo_normativo
    atende_ac_maximo = ac_efetivo <= ac_max_durabilidade
    conforme_todas = (
        atende_resistencia_minima and atende_consumo_minimo and atende_ac_maximo
    )

    verificacoes = VerificacoesNormativas(
        fcm_calculado_mpa=fcm,
        desvio_padrao_adotado_mpa=sd,
        ac_resistencia=ac_resistencia,
        ac_durabilidade_limite=ac_max_durabilidade,
        ac_adotado=ac_efetivo,
        motivo_escolha_ac=motivo_ac,
        consumo_cimento_minimo_normativo=consumo_cimento_minimo_normativo,
        consumo_cimento_calculado=consumo_cimento_calculado,
        fck_minimo_normativo=fck_min_durabilidade,
        atende_resistencia_minima=atende_resistencia_minima,
        atende_consumo_minimo=atende_consumo_minimo,
        atende_relacao_ac_maxima=atende_ac_maximo,
        conforme_todas_normas=conforme_todas,
    )

    return ResultadoDosagem(
        parametros=params,
        fck_solicitado_mpa=params.fck_mpa,
        fcm_dosagem_mpa=fcm,
        slump_adotado_mm=params.slump_mm,
        consumos_m3=consumos_m3,
        traco_seco=traco_seco,
        ajuste_canteiro=ajuste_canteiro,
        custos=custos,
        verificacoes=verificacoes,
        avisos=tuple(avisos),
    )
