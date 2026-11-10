"""Exportadores de relatórios em Markdown, CSV e SVG vetorial 1440x900.

LOFRANO TECNOLOGIA.
Proteção estrita contra injeção de fórmulas CSV. Aritmética 100% inteira/racional.
"""

from fractions import Fraction
import html
from typing import Any

from .domain import ResultadoDosagem
from .formatters import (
    formatar_fracao_decimal,
    formatar_moeda,
    formatar_traco_saco_50kg,
    formatar_traco_unitario,
)


CARACTERES_INJECAO_CSV: tuple[str, ...] = ("=", "+", "-", "@", "\t", "\r")


def sanitizar_campo_csv(valor: Any) -> str:
    """Sanitiza campos contra injeção de fórmulas em planilhas eletrônicas (CSV Injection).

    Se o valor iniciar com '=', '+', '-', '@', '\\t' ou '\\r', prefixa com aspa simples (').
    """
    if valor is None:
        return ""
    texto = str(valor)
    if not texto:
        return ""
    if texto.startswith(CARACTERES_INJECAO_CSV):
        return f"'{texto}"
    return texto


def gerar_markdown(res: ResultadoDosagem) -> str:
    """Gera relatório técnico detalhado em Markdown."""
    p = res.parametros
    c = res.consumos_m3
    t = res.traco_seco
    a = res.ajuste_canteiro
    cu = res.custos
    v = res.verificacoes

    linhas: list[str] = [
        f"# Memorial de Cálculo de Dosagem de Concreto — Método ABCP/ACI",
        f"",
        f"**Identificação do Projeto:** {res.identificacao}  ",
        f"**Normas de Referência:** ABNT NBR 12655:2022, ABNT NBR 6118:2023 e Método ABCP/ACI  ",
        f"**Engenharia Responsável:** Lofrano Tecnologia  ",
        f"",
        f"---",
        f"",
        f"## 1. Parâmetros de Entrada e Condições Normativas",
        f"",
        f"| Parâmetro | Valor Informado | Unidade / Critério |",
        f"|---|---|---|",
        f"| Resistência Característica ($f_{{ck}}$) | {formatar_fracao_decimal(res.fck_solicitado_mpa, 2)} | MPa |",
        f"| Condição de Preparo | {p.condicao_preparo.value} | Desvio-Padrão $s_d = {formatar_fracao_decimal(v.desvio_padrao_adotado_mpa, 2)}$ MPa |",
        f"| Classe de Agressividade Ambiental (CAA) | {p.classe_agressividade.value} | NBR 6118 / NBR 12655 |",
        f"| Tipo de Estrutura | {p.tipo_estrutura.value.replace('_', ' ')} | Limites de cobrimento e durabilidade |",
        f"| Consistência (Slump test) | {res.slump_adotado_mm} | mm (Abatimento do tronco de cone) |",
        f"| Tipo de Cimento Portland | {p.cimento.tipo.value} | $\\gamma = {formatar_fracao_decimal(p.cimento.massa_especifica_real_kg_l, 2)}$ kg/L |",
        f"| Agregado Miúdo (Areia) | {p.areia.nome} | MF = {formatar_fracao_decimal(p.areia.modulo_finura, 2)}, $\\gamma = {formatar_fracao_decimal(p.areia.massa_especifica_real_kg_l, 2)}$ kg/L |",
    ]

    for b in p.britas:
        linhas.append(
            f"| Agregado Graúdo ({b.nome}) | $d_{{max}} = {formatar_fracao_decimal(b.d_max_mm, 1)}$ mm | "
            f"$\\gamma_{{unit}} = {formatar_fracao_decimal(b.massa_unitaria_compactada_kg_m3, 0)}$ kg/m³, "
            f"$\\gamma_{{real}} = {formatar_fracao_decimal(b.massa_especifica_real_kg_l, 2)}$ kg/L |"
        )

    linhas.extend([
        f"",
        f"---",
        f"",
        f"## 2. Resistência de Dosagem e Relação Água/Cimento ($a/c$)",
        f"",
        f"- **Resistência Média de Dosagem ($f_{{cm}}$):**  ",
        f"  $$f_{{cm}} = f_{{ck}} + 1,65 \\times s_d = {formatar_fracao_decimal(res.fck_solicitado_mpa, 2)} + 1,65 \\times {formatar_fracao_decimal(v.desvio_padrao_adotado_mpa, 2)} = \\mathbf{{{formatar_fracao_decimal(res.fcm_dosagem_mpa, 2)} \\text{{ MPa}}}}$$  ",
        f"- **Relação $a/c$ por Resistência Mecânica (Curva de Abrams):** {formatar_fracao_decimal(v.ac_resistencia, 3)}  ",
        f"- **Relação $a/c$ Limite por Durabilidade (CAA {p.classe_agressividade.value}):** {formatar_fracao_decimal(v.ac_durabilidade_limite, 3)}  ",
        f"- **Relação $a/c$ Adotada:** $\\mathbf{{{formatar_fracao_decimal(v.ac_adotado, 3)}}}$  ",
        f"  *Critério:* {v.motivo_escolha_ac}  ",
        f"",
        f"---",
        f"",
        f"## 3. Consumos de Materiais para 1 Metro Cúbico (1000 Litros)",
        f"",
        f"| Material | Consumo em Massa | Volume Absoluto | Proporção / Detalhes |",
        f"|---|---|---|---|",
        f"| **Cimento Portland** | **{formatar_fracao_decimal(c.cimento_kg, 2)} kg** | {formatar_fracao_decimal(c.volume_cimento_litros, 2)} L | {formatar_fracao_decimal(c.sacos_cimento_50kg, 2)} sacos de 50 kg |",
        f"| **Água de Amassamento** | **{formatar_fracao_decimal(c.agua_litros, 2)} L** | {formatar_fracao_decimal(c.volume_agua_litros, 2)} L | Slump {res.slump_adotado_mm} mm |",
        f"| **Areia Seca** | **{formatar_fracao_decimal(c.areia_kg, 2)} kg** | {formatar_fracao_decimal(c.volume_areia_litros, 2)} L | Balanço de volume absoluto |",
    ])

    for (nome, massa), (_, vol) in zip(c.britas_kg, c.volumes_brita_litros):
        linhas.append(
            f"| **Brita Seca ({nome})** | **{formatar_fracao_decimal(massa, 2)} kg** | {formatar_fracao_decimal(vol, 2)} L | Método ABCP ($V_{{ob}}$) |"
        )

    if c.aditivo_kg > Fraction(0):
        linhas.append(
            f"| **Aditivo Químico** | **{formatar_fracao_decimal(c.aditivo_kg, 2)} kg** | {formatar_fracao_decimal(c.volume_aditivo_litros, 2)} L | Dosagem especial |"
        )

    linhas.extend([
        f"| **Ar Aprisionado** | — | {formatar_fracao_decimal(c.ar_aprisionado_litros, 2)} L | Estimativa natural ABCP |",
        f"| **TOTAL ABSOLUTO** | **{formatar_fracao_decimal(c.massa_especifica_fresca_kg_m3, 2)} kg/m³** | **{formatar_fracao_decimal(c.volume_absoluto_total_litros, 1)} L** | Massa fresca estimada |",
        f"",
        f"---",
        f"",
        f"## 4. Traço Unitário em Massa Seca",
        f"",
        f"$$\\mathbf{{{formatar_traco_unitario(t)}}}$$",
        f"",
        f"- **Cimento:** 1,00",
        f"- **Areia ($m_a$):** {formatar_fracao_decimal(t.areia, 2)}",
        f"- **Brita Total ($m_b$):** {formatar_fracao_decimal(t.brita_total, 2)}",
        f"- **Relação Água/Cimento ($a/c$):** {formatar_fracao_decimal(t.agua_cimento, 2)}",
        f"- **Soma dos Agregados ($m = m_a + m_b$):** {formatar_fracao_decimal(t.soma_agregados_m, 2)}",
        f"- **Teor de Argamassa Seca ($\\alpha$):** {formatar_fracao_decimal(t.teor_argamassa_pct, 1)}\\%",
        f"",
        f"---",
        f"",
        f"## 5. Ajuste Operacional para Canteiro de Obras (Correção de Umidade)",
        f"",
        f"Considerando a umidade superficial da areia de **{formatar_fracao_decimal(p.areia.umidade_pct, 1)}\\%** "
        f"e dos agregados graúdos:",
        f"",
        f"- **Água fornecida pelos agregados:** {formatar_fracao_decimal(a.agua_contida_agregados_litros_m3, 2)} L/m³  ",
        f"- **Água efetiva a adicionar na betoneira:** {formatar_fracao_decimal(a.agua_efetiva_litros_m3, 2)} L/m³  ",
        f"- **Areia úmida necessária:** {formatar_fracao_decimal(a.areia_umida_kg_m3, 2)} kg/m³  ",
        f"",
        f"### Proporção por Saco de Cimento de 50 kg:",
        f"$$\\mathbf{{{formatar_traco_saco_50kg(a)}}}$$",
        f"",
    ])

    if a.volume_areia_padiolas_litros is not None:
        linhas.append(
            f"- **Volume aparente de areia úmida (padiolas):** {formatar_fracao_decimal(a.volume_areia_padiolas_litros, 1)} L por saco de cimento"
        )
    if a.volumes_brita_padiolas_litros is not None:
        for nome, vol in a.volumes_brita_padiolas_litros:
            linhas.append(
                f"- **Volume aparente de brita ({nome}):** {formatar_fracao_decimal(vol, 1)} L por saco de cimento"
            )

    linhas.extend([
        f"",
        f"---",
        f"",
        f"## 6. Estimativa de Custos dos Materiais",
        f"",
        f"| Insumo | Custo por m³ de Concreto |",
        f"|---|---|",
        f"| Cimento Portland | {formatar_moeda(cu.custo_cimento_m3)} |",
        f"| Areia | {formatar_moeda(cu.custo_areia_m3)} |",
        f"| Brita | {formatar_moeda(cu.custo_brita_m3)} |",
        f"| Água | {formatar_moeda(cu.custo_agua_m3)} |",
        f"| Aditivo | {formatar_moeda(cu.custo_aditivo_m3)} |",
        f"| **TOTAL POR METRO CÚBICO** | **{formatar_moeda(cu.custo_total_m3)}** |",
        f"| **TOTAL POR SACO DE CIMENTO (50 kg)** | **{formatar_moeda(cu.custo_por_saco_cimento)}** |",
        f"",
        f"---",
        f"",
        f"## 7. Quadro de Conformidade Normativa (NBR 12655 / NBR 6118)",
        f"",
        f"- Resistência mínima da CAA ({formatar_fracao_decimal(v.fck_minimo_normativo, 1)} MPa): "
        f"{'CONFORME [OK]' if v.atende_resistencia_minima else 'NÃO CONFORME [ATENÇÃO]'}  ",
        f"- Relação a/c máxima da CAA ({formatar_fracao_decimal(v.ac_durabilidade_limite, 2)}): "
        f"{'CONFORME [OK]' if v.atende_relacao_ac_maxima else 'NÃO CONFORME [ATENÇÃO]'}  ",
        f"- Consumo mínimo de cimento ({formatar_fracao_decimal(v.consumo_cimento_minimo_normativo, 0)} kg/m³): "
        f"{'CONFORME [OK]' if v.atende_consumo_minimo else 'NÃO CONFORME [ATENÇÃO]'}  ",
        f"",
    ])

    if res.avisos:
        linhas.append("### Observações e Alertas Técnicos:")
        for aviso in res.avisos:
            linhas.append(f"- ⚠️ {aviso}")
        linhas.append("")

    return "\n".join(linhas) + "\n"


def gerar_csv(res: ResultadoDosagem) -> str:
    """Gera dados de dosagem em formato CSV delimitado por ponto e vírgula com sanitização."""
    p = res.parametros
    c = res.consumos_m3
    t = res.traco_seco
    a = res.ajuste_canteiro
    cu = res.custos
    v = res.verificacoes

    linhas: list[list[str]] = [
        ["RELATORIO DE DOSAGEM DE CONCRETO - METODO ABCP/ACI", "LOFRANO TECNOLOGIA"],
        ["Identificacao", res.identificacao],
        ["Normas", "ABNT NBR 12655:2022 / ABNT NBR 6118:2023"],
        [],
        ["PARAMETROS DE ENTRADA", "VALOR", "UNIDADE"],
        ["fck solicitado", formatar_fracao_decimal(res.fck_solicitado_mpa, 2), "MPa"],
        ["Condicao de Preparo", p.condicao_preparo.value, "NBR 12655"],
        ["Desvio Padrao (sd)", formatar_fracao_decimal(v.desvio_padrao_adotado_mpa, 2), "MPa"],
        ["Resistencia de Dosagem (fcm)", formatar_fracao_decimal(res.fcm_dosagem_mpa, 2), "MPa"],
        ["Classe de Agressividade Ambiental", p.classe_agressividade.value, "NBR 6118"],
        ["Tipo de Estrutura", p.tipo_estrutura.value, ""],
        ["Slump (Abatimento)", str(res.slump_adotado_mm), "mm"],
        ["Tipo de Cimento", p.cimento.tipo.value, ""],
        ["Relacao a/c Adotada", formatar_fracao_decimal(v.ac_adotado, 3), ""],
        ["Criterio a/c", v.motivo_escolha_ac, ""],
        [],
        ["TRACO UNITARIO EM MASSA SECA", "PROPORCAO"],
        ["Cimento", "1,00"],
        ["Areia (ma)", formatar_fracao_decimal(t.areia, 2)],
        ["Brita Total (mb)", formatar_fracao_decimal(t.brita_total, 2)],
        ["Agua/Cimento (a/c)", formatar_fracao_decimal(t.agua_cimento, 2)],
        ["Soma Agregados (m)", formatar_fracao_decimal(t.soma_agregados_m, 2)],
        ["Teor Argamassa Seca (%)", formatar_fracao_decimal(t.teor_argamassa_pct, 1)],
        [],
        ["CONSUMOS POR METRO CUBICO", "MASSA (kg/m3)", "VOLUME ABSOLUTO (L/m3)"],
        ["Cimento", formatar_fracao_decimal(c.cimento_kg, 2), formatar_fracao_decimal(c.volume_cimento_litros, 2)],
        ["Agua", formatar_fracao_decimal(c.agua_litros, 2), formatar_fracao_decimal(c.volume_agua_litros, 2)],
        ["Areia Seca", formatar_fracao_decimal(c.areia_kg, 2), formatar_fracao_decimal(c.volume_areia_litros, 2)],
    ]

    for (nome, massa), (_, vol) in zip(c.britas_kg, c.volumes_brita_litros):
        linhas.append([f"Brita ({nome})", formatar_fracao_decimal(massa, 2), formatar_fracao_decimal(vol, 2)])

    if c.aditivo_kg > Fraction(0):
        linhas.append(["Aditivo", formatar_fracao_decimal(c.aditivo_kg, 2), formatar_fracao_decimal(c.volume_aditivo_litros, 2)])

    linhas.append(["Ar Aprisionado", "0,00", formatar_fracao_decimal(c.ar_aprisionado_litros, 2)])
    linhas.append(["Total Concreto Fresco", formatar_fracao_decimal(c.massa_especifica_fresca_kg_m3, 2), formatar_fracao_decimal(c.volume_absoluto_total_litros, 1)])
    linhas.append([])
    linhas.append(["AJUSTE DE CANTEIRO (POR SACO 50 kg DE CIMENTO)", "QUANTIDADE", "UNIDADE"])
    linhas.append(["Cimento (1 saco)", formatar_fracao_decimal(a.traco_saco_50kg_cimento_kg, 1), "kg"])
    linhas.append(["Areia Umida", formatar_fracao_decimal(a.traco_saco_50kg_areia_umida_kg, 1), "kg"])

    for nome, massa in a.traco_saco_50kg_britas_umidas_kg:
        linhas.append([f"Brita Umida ({nome})", formatar_fracao_decimal(massa, 1), "kg"])

    linhas.append(["Agua a Adicionar", formatar_fracao_decimal(a.traco_saco_50kg_agua_litros, 1), "Litros"])
    linhas.append([])
    linhas.append(["CUSTOS ESTIMADOS", "VALOR (R$)"])
    linhas.append(["Custo Cimento por m3", formatar_moeda(cu.custo_cimento_m3)])
    linhas.append(["Custo Areia por m3", formatar_moeda(cu.custo_areia_m3)])
    linhas.append(["Custo Brita por m3", formatar_moeda(cu.custo_brita_m3)])
    linhas.append(["Custo Agua por m3", formatar_moeda(cu.custo_agua_m3)])
    linhas.append(["Custo Aditivo por m3", formatar_moeda(cu.custo_aditivo_m3)])
    linhas.append(["Custo Total por m3", formatar_moeda(cu.custo_total_m3)])
    linhas.append(["Custo por Saco de Cimento (50 kg)", formatar_moeda(cu.custo_por_saco_cimento)])

    linhas_texto: list[str] = []
    for l in linhas:
        cols_sanitizadas = []
        for col in l:
            s = sanitizar_campo_csv(col)
            if ";" in s or '"' in s or "\n" in s:
                s = '"' + s.replace('"', '""') + '"'
            cols_sanitizadas.append(s)
        linhas_texto.append(";".join(cols_sanitizadas))

    return "\n".join(linhas_texto) + "\n"


def gerar_painel_svg(res: ResultadoDosagem) -> str:
    """Gera painel visual vetorial de 1440x900 pixels em SVG com arquitetura gráfica da Lofrano Tecnologia."""
    p = res.parametros
    c = res.consumos_m3
    t = res.traco_seco
    a = res.ajuste_canteiro
    cu = res.custos
    v = res.verificacoes

    largura = 1440
    altura = 900

    str_fck = formatar_fracao_decimal(res.fck_solicitado_mpa, 1)
    str_fcm = formatar_fracao_decimal(res.fcm_dosagem_mpa, 1)
    str_sd = formatar_fracao_decimal(v.desvio_padrao_adotado_mpa, 1)
    str_ac = formatar_fracao_decimal(v.ac_adotado, 2)
    str_traco = formatar_traco_unitario(t)
    str_custo_m3 = formatar_moeda(cu.custo_total_m3)
    str_custo_saco = formatar_moeda(cu.custo_por_saco_cimento)
    str_massa_fresca = formatar_fracao_decimal(c.massa_especifica_fresca_kg_m3, 0)
    str_cimento_kg = formatar_fracao_decimal(c.cimento_kg, 1)
    str_agua_l = formatar_fracao_decimal(c.agua_litros, 1)
    str_areia_kg = formatar_fracao_decimal(c.areia_kg, 1)
    str_brita_kg = formatar_fracao_decimal(c.brita_total_kg, 1)

    # Proporções de volume para o gráfico de barras fechando em 1000 Litros
    vol_c = int(c.volume_cimento_litros)
    vol_a = int(c.volume_agua_litros)
    vol_ar = int(c.ar_aprisionado_litros)
    vol_b = int(c.volume_brita_total_litros)
    vol_s = int(c.volume_areia_litros)
    largura_barra_total = 540

    w_c = max(10, (vol_c * largura_barra_total) // 1000)
    w_a = max(10, (vol_a * largura_barra_total) // 1000)
    w_ar = max(5, (vol_ar * largura_barra_total) // 1000)
    w_b = max(10, (vol_b * largura_barra_total) // 1000)
    w_s = largura_barra_total - (w_c + w_a + w_ar + w_b)

    status_cor = "#10b981" if v.conforme_todas_normas else "#f59e0b"
    status_txt = "CONFORME NBR 12655 / NBR 6118" if v.conforme_todas_normas else "ATENÇÃO NORMATIVA"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" width="{largura}" height="{altura}">
  <defs>
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#1e293b" />
    </linearGradient>
    <linearGradient id="card-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1e293b" stop-opacity="0.9" />
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.95" />
    </linearGradient>
    <linearGradient id="accent-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#6366f1" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity="0.4" />
    </filter>
  </defs>

  <!-- Fundo Principal -->
  <rect width="{largura}" height="{altura}" fill="url(#bg-grad)" />

  <!-- Cabeçalho -->
  <g transform="translate(60, 45)">
    <rect x="0" y="0" width="8" height="52" fill="url(#accent-grad)" rx="4" />
    <text x="24" y="24" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="800" fill="#f8fafc" letter-spacing="0.5">
      DOSAGEM DE CONCRETO · MÉTODO ABCP / ACI
    </text>
    <text x="24" y="46" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="500" fill="#94a3b8">
      {html.escape(res.identificacao)} | ABNT NBR 12655:2022 &amp; NBR 6118:2023 | LOFRANO TECNOLOGIA
    </text>
    
    <!-- Badge de Status -->
    <rect x="980" y="8" width="340" height="36" rx="18" fill="{status_cor}" fill-opacity="0.15" stroke="{status_cor}" stroke-width="1.5" />
    <circle cx="1004" cy="26" r="6" fill="{status_cor}" />
    <text x="1022" y="31" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="700" fill="{status_cor}" letter-spacing="0.5">
      {status_txt}
    </text>
  </g>

  <!-- Grid de Cards -->
  <!-- Card 1: Resistência e Durabilidade -->
  <g transform="translate(60, 125)" filter="url(#shadow)">
    <rect width="410" height="235" rx="12" fill="url(#card-grad)" stroke="#334155" stroke-width="1" />
    <text x="25" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="15" font-weight="700" fill="#38bdf8" letter-spacing="0.5">
      RESISTÊNCIA &amp; DURABILIDADE
    </text>

    <!-- fck e fcm -->
    <text x="25" y="82" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#94a3b8">fck PROJETO</text>
    <text x="25" y="118" font-family="ui-monospace, monospace" font-size="34" font-weight="800" fill="#f8fafc">{str_fck}</text>
    <text x="120" y="115" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="500" fill="#64748b">MPa</text>

    <text x="215" y="82" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#94a3b8">fcm DOSAGEM (sd={str_sd})</text>
    <text x="215" y="118" font-family="ui-monospace, monospace" font-size="34" font-weight="800" fill="#38bdf8">{str_fcm}</text>
    <text x="310" y="115" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="500" fill="#64748b">MPa</text>

    <line x1="25" y1="145" x2="385" y2="145" stroke="#334155" stroke-width="1" />

    <text x="25" y="175" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="500" fill="#cbd5e1">
      Condição de Preparo: <tspan font-weight="700" fill="#f8fafc">{p.condicao_preparo.value}</tspan>
    </text>
    <text x="25" y="202" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="500" fill="#cbd5e1">
      Classe Agressividade: <tspan font-weight="700" fill="#f8fafc">{p.classe_agressividade.value}</tspan> (máx a/c: {formatar_fracao_decimal(v.ac_durabilidade_limite, 2)})
    </text>
  </g>

  <!-- Card 2: Traço Unitário em Massa Seca -->
  <g transform="translate(500, 125)" filter="url(#shadow)">
    <rect width="440" height="235" rx="12" fill="url(#card-grad)" stroke="#334155" stroke-width="1" />
    <text x="25" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="15" font-weight="700" fill="#38bdf8" letter-spacing="0.5">
      TRAÇO UNITÁRIO EM MASSA SECA
    </text>

    <!-- Fórmula do Traço -->
    <rect x="25" y="60" width="390" height="60" rx="8" fill="#0f172a" stroke="#1e293b" />
    <text x="220" y="100" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="800" fill="#f8fafc">
      {str_traco}
    </text>

    <text x="25" y="152" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="500" fill="#cbd5e1">
      Relação a/c adotada: <tspan font-weight="700" fill="#38bdf8">{str_ac}</tspan>
    </text>
    <text x="25" y="177" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="500" fill="#cbd5e1">
      Soma agregados (m): <tspan font-weight="700" fill="#f8fafc">{formatar_fracao_decimal(t.soma_agregados_m, 2)}</tspan>
    </text>
    <text x="25" y="202" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="500" fill="#cbd5e1">
      Teor de argamassa seca (α): <tspan font-weight="700" fill="#f8fafc">{formatar_fracao_decimal(t.teor_argamassa_pct, 1)}%</tspan>
    </text>
  </g>

  <!-- Card 3: Custos e Orçamentação -->
  <g transform="translate(970, 125)" filter="url(#shadow)">
    <rect width="410" height="235" rx="12" fill="url(#card-grad)" stroke="#334155" stroke-width="1" />
    <text x="25" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="15" font-weight="700" fill="#38bdf8" letter-spacing="0.5">
      ORÇAMENTAÇÃO &amp; CUSTO DE INSUMOS
    </text>

    <text x="25" y="82" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#94a3b8">CUSTO POR METRO CÚBICO</text>
    <text x="25" y="118" font-family="ui-monospace, monospace" font-size="32" font-weight="800" fill="#10b981">{str_custo_m3}</text>

    <text x="25" y="152" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#94a3b8">CUSTO POR SACO DE CIMENTO (50 kg)</text>
    <text x="25" y="186" font-family="ui-monospace, monospace" font-size="26" font-weight="700" fill="#38bdf8">{str_custo_saco}</text>

    <text x="25" y="215" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="500" fill="#64748b">
      Massa fresca estimada: {str_massa_fresca} kg/m³
    </text>
  </g>

  <!-- Card 4: Consumos e Balanço Volumétrico Absoluto (1 m³ = 1000 Litros) -->
  <g transform="translate(60, 390)" filter="url(#shadow)">
    <rect width="660" height="460" rx="12" fill="url(#card-grad)" stroke="#334155" stroke-width="1" />
    <text x="30" y="42" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="700" fill="#38bdf8" letter-spacing="0.5">
      CONSUMOS POR METRO CÚBICO &amp; VOLUME ABSOLUTO (1000 L)
    </text>

    <!-- Gráfico de Barra Proporcional de Volume Absoluto -->
    <g transform="translate(30, 70)">
      <rect x="0" y="0" width="{largura_barra_total}" height="32" rx="6" fill="#0f172a" />
      <rect x="0" y="0" width="{w_c}" height="32" rx="6" fill="#6366f1" />
      <rect x="{w_c}" y="0" width="{w_a}" height="32" fill="#0ea5e9" />
      <rect x="{w_c + w_a}" y="0" width="{w_ar}" height="32" fill="#94a3b8" />
      <rect x="{w_c + w_a + w_ar}" y="0" width="{w_s}" height="32" fill="#eab308" />
      <rect x="{w_c + w_a + w_ar + w_s}" y="0" width="{w_b}" height="32" rx="6" fill="#10b981" />
    </g>

    <!-- Legenda de Cores -->
    <g transform="translate(30, 120)" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600">
      <circle cx="6" cy="6" r="6" fill="#6366f1" />
      <text x="20" y="10" fill="#cbd5e1">Cimento ({vol_c} L)</text>

      <circle cx="150" cy="6" r="6" fill="#0ea5e9" />
      <text x="164" y="10" fill="#cbd5e1">Água ({vol_a} L)</text>

      <circle cx="280" cy="6" r="6" fill="#eab308" />
      <text x="294" y="10" fill="#cbd5e1">Areia ({vol_s} L)</text>

      <circle cx="420" cy="6" r="6" fill="#10b981" />
      <text x="434" y="10" fill="#cbd5e1">Brita ({vol_b} L)</text>

      <circle cx="530" cy="6" r="6" fill="#94a3b8" />
      <text x="544" y="10" fill="#cbd5e1">Ar ({vol_ar} L)</text>
    </g>

    <!-- Tabela de Consumos -->
    <g transform="translate(30, 160)" font-family="system-ui, -apple-system, sans-serif">
      <rect x="0" y="0" width="600" height="34" rx="4" fill="#0f172a" />
      <text x="20" y="22" font-size="12" font-weight="700" fill="#94a3b8">MATERIAL</text>
      <text x="260" y="22" font-size="12" font-weight="700" fill="#94a3b8">MASSA SECA</text>
      <text x="440" y="22" font-size="12" font-weight="700" fill="#94a3b8">VOLUME REAL</text>

      <!-- Linha Cimento -->
      <text x="20" y="65" font-size="14" font-weight="600" fill="#f8fafc">Cimento Portland</text>
      <text x="260" y="65" font-family="ui-monospace, monospace" font-size="15" font-weight="700" fill="#38bdf8">{str_cimento_kg} kg</text>
      <text x="440" y="65" font-family="ui-monospace, monospace" font-size="14" fill="#94a3b8">{vol_c} L ({formatar_fracao_decimal(c.sacos_cimento_50kg, 1)} sacos)</text>

      <!-- Linha Água -->
      <text x="20" y="105" font-size="14" font-weight="600" fill="#f8fafc">Água Amassamento</text>
      <text x="260" y="105" font-family="ui-monospace, monospace" font-size="15" font-weight="700" fill="#38bdf8">{str_agua_l} L</text>
      <text x="440" y="105" font-family="ui-monospace, monospace" font-size="14" fill="#94a3b8">{vol_a} L (Slump {res.slump_adotado_mm} mm)</text>

      <!-- Linha Areia -->
      <text x="20" y="145" font-size="14" font-weight="600" fill="#f8fafc">Agregado Miúdo (Areia)</text>
      <text x="260" y="145" font-family="ui-monospace, monospace" font-size="15" font-weight="700" fill="#38bdf8">{str_areia_kg} kg</text>
      <text x="440" y="145" font-family="ui-monospace, monospace" font-size="14" fill="#94a3b8">{vol_s} L (Balanço vol.)</text>

      <!-- Linha Brita -->
      <text x="20" y="185" font-size="14" font-weight="600" fill="#f8fafc">Agregado Graúdo (Brita)</text>
      <text x="260" y="185" font-family="ui-monospace, monospace" font-size="15" font-weight="700" fill="#38bdf8">{str_brita_kg} kg</text>
      <text x="440" y="185" font-family="ui-monospace, monospace" font-size="14" fill="#94a3b8">{vol_b} L (Método ABCP)</text>

      <!-- Linha Ar -->
      <text x="20" y="225" font-size="14" font-weight="600" fill="#f8fafc">Ar Aprisionado</text>
      <text x="260" y="225" font-family="ui-monospace, monospace" font-size="15" font-weight="500" fill="#64748b">—</text>
      <text x="440" y="225" font-family="ui-monospace, monospace" font-size="14" fill="#94a3b8">{vol_ar} L (Teor natural)</text>

      <line x1="0" y1="245" x2="600" y2="245" stroke="#334155" stroke-width="1" />

      <!-- Linha Total -->
      <text x="20" y="275" font-size="15" font-weight="800" fill="#f8fafc">TOTAL 1 m³ CONCRETO</text>
      <text x="260" y="275" font-family="ui-monospace, monospace" font-size="16" font-weight="800" fill="#10b981">{str_massa_fresca} kg</text>
      <text x="440" y="275" font-family="ui-monospace, monospace" font-size="16" font-weight="800" fill="#10b981">1.000,0 L</text>
    </g>
  </g>

  <!-- Card 5: Operação de Canteiro (Ajuste de Umidade por Saco de 50 kg) -->
  <g transform="translate(750, 390)" filter="url(#shadow)">
    <rect width="630" height="460" rx="12" fill="url(#card-grad)" stroke="#334155" stroke-width="1" />
    <text x="30" y="42" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="700" fill="#38bdf8" letter-spacing="0.5">
      OPERAÇÃO EM CANTEIRO · PROPORÇÃO POR SACO DE CIMENTO (50 kg)
    </text>

    <!-- Caixa de Destaque do Traço de Canteiro -->
    <rect x="30" y="65" width="570" height="90" rx="8" fill="#0f172a" stroke="#1e293b" />
    <text x="50" y="95" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="600" fill="#94a3b8">
      CORREÇÃO DE UMIDADE (Areia: {formatar_fracao_decimal(p.areia.umidade_pct, 1)}% | Brita: {formatar_fracao_decimal(p.britas[0].umidade_pct, 1)}%)
    </text>
    <text x="50" y="132" font-family="ui-monospace, monospace" font-size="17" font-weight="700" fill="#f8fafc">
      {formatar_traco_saco_50kg(a)}
    </text>

    <!-- Itens detalhados por saco -->
    <g transform="translate(30, 185)" font-family="system-ui, -apple-system, sans-serif">
      <rect x="0" y="0" width="270" height="110" rx="8" fill="#1e293b" stroke="#334155" />
      <text x="20" y="30" font-size="13" font-weight="700" fill="#eab308">AREIA ÚMIDA</text>
      <text x="20" y="65" font-family="ui-monospace, monospace" font-size="28" font-weight="800" fill="#f8fafc">
        {formatar_fracao_decimal(a.traco_saco_50kg_areia_umida_kg, 1)}
      </text>
      <text x="120" y="62" font-size="14" font-weight="500" fill="#64748b">kg / saco</text>
      <text x="20" y="95" font-size="12" fill="#94a3b8">
        Água agregados: {formatar_fracao_decimal(a.agua_contida_agregados_litros_m3, 1)} L/m³
      </text>

      <rect x="300" y="0" width="270" height="110" rx="8" fill="#1e293b" stroke="#334155" />
      <text x="320" y="30" font-size="13" font-weight="700" fill="#10b981">BRITA ÚMIDA</text>
      <text x="320" y="65" font-family="ui-monospace, monospace" font-size="28" font-weight="800" fill="#f8fafc">
        {formatar_fracao_decimal(a.traco_saco_50kg_britas_umidas_kg[0][1], 1)}
      </text>
      <text x="420" y="62" font-size="14" font-weight="500" fill="#64748b">kg / saco</text>
      <text x="320" y="95" font-size="12" fill="#94a3b8">
        Água efetiva betoneira: {formatar_fracao_decimal(a.traco_saco_50kg_agua_litros, 1)} L
      </text>
    </g>

    <!-- Padiolas se disponíveis -->
    <g transform="translate(30, 320)" font-family="system-ui, -apple-system, sans-serif">
      <rect x="0" y="0" width="570" height="95" rx="8" fill="#0f172a" stroke="#1e293b" />
      <text x="25" y="30" font-size="13" font-weight="700" fill="#38bdf8">DIMENSIONAMENTO DE PADIOLAS EM VOLUME (LITROS)</text>
      <text x="25" y="58" font-size="13" fill="#cbd5e1">
        • Areia úmida por saco de cimento: <tspan font-weight="700" fill="#f8fafc">{formatar_fracao_decimal(a.volume_areia_padiolas_litros or 0, 1)} Litros</tspan>
      </text>
      <text x="25" y="80" font-size="13" fill="#cbd5e1">
        • Brita compactada/solta por saco de cimento: <tspan font-weight="700" fill="#f8fafc">{formatar_fracao_decimal(a.volumes_brita_padiolas_litros[0][1] if a.volumes_brita_padiolas_litros else 0, 1)} Litros</tspan>
      </text>
    </g>
  </g>
</svg>
"""
    return svg
