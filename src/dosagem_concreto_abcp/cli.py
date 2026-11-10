"""Interface de Linha de Comando (CLI) para dosagem de concreto ABCP.

LOFRANO TECNOLOGIA.
Subcomandos: calcular, modelo, tabelas, versao.
"""

import argparse
from pathlib import Path
import sys

from . import __version__
from .calculator import calcular_dosagem_abcp
from .constants import (
    LIMITES_CAA,
    REGRAS_CONDICAO_PREPARO,
    TABELA_CONSUMO_AGUA_ABCP,
    TABELA_VOLUME_APARENTE_BRITA,
)
from .errors import ErroDosagemConcreto
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


def gerar_modelo_exemplo_dict() -> dict:
    """Retorna dicionário de exemplo completo pronto para serialização JSON."""
    return {
        "identificacao": "Concreto C25 Convencional para Edificação Residencial",
        "fck_mpa": 25,
        "condicao_preparo": "A",
        "classe_agressividade": "CAA_II",
        "tipo_estrutura": "CONCRETO_ARMADO",
        "slump_mm": 80,
        "cimento": {
            "tipo": "CP_II_32",
            "massa_especifica_real_kg_l": "3.15",
            "consumo_minimo_especifico_kg_m3": 280,
        },
        "areia": {
            "nome": "Areia Média Lavada",
            "modulo_finura": "2.40",
            "massa_especifica_real_kg_l": "2.63",
            "massa_unitaria_solta_kg_m3": 1420,
            "umidade_pct": "3.0",
            "inchamento_coeficiente": "1.25",
            "absorcao_pct": "0.8",
        },
        "britas": [
            {
                "nome": "Brita 1 (19 mm)",
                "d_max_mm": "19.0",
                "massa_unitaria_compactada_kg_m3": 1500,
                "massa_especifica_real_kg_l": "2.68",
                "massa_unitaria_solta_kg_m3": 1420,
                "umidade_pct": "0.5",
                "absorcao_pct": "0.5",
                "proporcao_mistura": 1,
            }
        ],
        "aditivo_redutor_agua_pct": "0.0",
        "dosagem_aditivo_pct_cimento": "0.0",
        "aditivo_densidade_kg_l": "1.0",
        "teor_ar_adicional_pct": "0.0",
        "precos": {
            "cimento_por_saco_50kg": "38.50",
            "areia_por_metro_cubico": "120.00",
            "brita_por_metro_cubico": "110.00",
            "agua_por_metro_cubico": "8.50",
            "aditivo_por_litro": "0.00",
        },
    }


def comando_calcular(args: argparse.Namespace) -> int:
    """Executa o cálculo de dosagem a partir do arquivo JSON fornecido."""
    caminho_entrada = Path(args.arquivo_entrada)
    if not caminho_entrada.exists():
        print(f"Erro: Arquivo de entrada '{caminho_entrada}' não encontrado.", file=sys.stderr)
        return 1

    try:
        conteudo_bytes = caminho_entrada.read_bytes()
        dado_json = decodificar_json_seguro(conteudo_bytes)
        params = carregar_parametros_json(dado_json)
        resultado = calcular_dosagem_abcp(params)
    except ErroDosagemConcreto as e:
        print(f"Erro de dosagem: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        return 3

    # Resumo no terminal
    t = resultado.traco_seco
    c = resultado.consumos_m3
    v = resultado.verificacoes
    a = resultado.ajuste_canteiro
    cu = resultado.custos

    print("=" * 72)
    print("DOSAGEM DE CONCRETO · MÉTODO ABCP/ACI (ABNT NBR 12655 / NBR 6118)")
    print(f"Identificação: {resultado.identificacao}")
    print("=" * 72)
    print(f"fck solicitado:       {formatar_fracao_decimal(resultado.fck_solicitado_mpa, 2)} MPa")
    print(f"Desvio-padrão (sd):   {formatar_fracao_decimal(v.desvio_padrao_adotado_mpa, 2)} MPa ({params.condicao_preparo.value})")
    print(f"fcm dosagem:          {formatar_fracao_decimal(resultado.fcm_dosagem_mpa, 2)} MPa")
    print(f"Relação a/c adotada:  {formatar_fracao_decimal(v.ac_adotado, 3)} ({v.motivo_escolha_ac})")
    print("-" * 72)
    print(f"TRAÇO SECO EM MASSA:  {formatar_traco_unitario(t)}")
    print(f"Soma agregados (m):   {formatar_fracao_decimal(t.soma_agregados_m, 2)}")
    print(f"Teor de argamassa:    {formatar_fracao_decimal(t.teor_argamassa_pct, 1)}%")
    print("-" * 72)
    print("CONSUMOS PARA 1 m³ DE CONCRETO:")
    print(f"  • Cimento:          {formatar_fracao_decimal(c.cimento_kg, 1)} kg ({formatar_fracao_decimal(c.sacos_cimento_50kg, 2)} sacos de 50 kg)")
    print(f"  • Água:             {formatar_fracao_decimal(c.agua_litros, 1)} L (Slump {resultado.slump_adotado_mm} mm)")
    print(f"  • Areia seca:       {formatar_fracao_decimal(c.areia_kg, 1)} kg")
    print(f"  • Brita seca total: {formatar_fracao_decimal(c.brita_total_kg, 1)} kg")
    print(f"  • Massa fresca:     {formatar_fracao_decimal(c.massa_especifica_fresca_kg_m3, 0)} kg/m³")
    print("-" * 72)
    print("CANTEIRO (POR SACO DE 50 kg COM CORREÇÃO DE UMIDADE):")
    print(f"  {formatar_traco_saco_50kg(a)}")
    print("-" * 72)
    print("CUSTOS ESTIMADOS:")
    print(f"  • Custo por m³:     {formatar_moeda(cu.custo_total_m3)}")
    print(f"  • Custo por saco:   {formatar_moeda(cu.custo_por_saco_cimento)}")
    print("=" * 72)

    if resultado.avisos:
        print("\nAlertas técnicos:")
        for av in resultado.avisos:
            print(f"  ⚠️ {av}")

    # Exportações
    dict_res = resultado_para_dict(resultado)
    str_json = serializar_json_canonico(dict_res)
    str_md = gerar_markdown(resultado)
    str_csv = gerar_csv(resultado)
    str_svg = gerar_painel_svg(resultado)

    if args.saida_json:
        p_json = Path(args.saida_json)
        p_json.write_text(str_json, encoding="utf-8")
        print(f"[+] Relatório JSON salvo em: {p_json}")

    if args.saida_md:
        p_md = Path(args.saida_md)
        p_md.write_text(str_md, encoding="utf-8")
        print(f"[+] Memorial Markdown salvo em: {p_md}")

    if args.saida_csv:
        p_csv = Path(args.saida_csv)
        p_csv.write_text(str_csv, encoding="utf-8")
        print(f"[+] Planilha CSV salva em: {p_csv}")

    if args.saida_svg:
        p_svg = Path(args.saida_svg)
        p_svg.write_text(str_svg, encoding="utf-8")
        print(f"[+] Painel visual SVG salvo em: {p_svg}")

    if args.saida_zip:
        p_zip = Path(args.saida_zip)
        arquivos_zip = {
            "caso_dosagem.json": str_json,
            "memorial_calculo.md": str_md,
            "tabela_consumos.csv": str_csv,
            "painel_visual.svg": str_svg,
        }
        hash_zip = salvar_zip_deterministico(p_zip, arquivos_zip, sobrescrever=args.sobrescrever)
        print(f"[+] Pacote determinístico ZIP salvo em: {p_zip} (SHA256: {hash_zip})")

    return 0


def comando_modelo(args: argparse.Namespace) -> int:
    """Gera um arquivo JSON modelo com caso de referência."""
    modelo = gerar_modelo_exemplo_dict()
    texto_json = serializar_json_canonico(modelo)

    if args.saida:
        p = Path(args.saida)
        p.write_text(texto_json, encoding="utf-8")
        print(f"[+] Modelo de dosagem salvo em: {p}")
    else:
        print(texto_json)
    return 0


def comando_tabelas(args: argparse.Namespace) -> int:
    """Exibe tabelas de referência normativa e empírica da ABCP e NBR."""
    print("=" * 72)
    print("TABELAS DE REFERÊNCIA · ABNT NBR 12655 / NBR 6118 / MÉTODO ABCP")
    print("=" * 72)
    print("\n1. Condições de Preparo (NBR 12655):")
    for k, v in REGRAS_CONDICAO_PREPARO.items():
        limite = f"fck <= {v.fck_max_mpa} MPa" if v.fck_max_mpa else "Sem limite superior"
        print(f"  • {v.nome}: sd = {formatar_fracao_decimal(v.desvio_padrao_mpa, 1)} MPa ({limite})")

    print("\n2. Classes de Agressividade Ambiental (NBR 6118 / NBR 12655):")
    for k, v in LIMITES_CAA.items():
        print(
            f"  • Classe {v.classe} ({v.agressividade}): máx a/c CA = {formatar_fracao_decimal(v.ac_maximo_ca, 2)}, "
            f"fck mín = {formatar_fracao_decimal(v.fck_minimo_ca, 0)} MPa, Cimento mín = {formatar_fracao_decimal(v.consumo_cimento_minimo_kg_m3, 0)} kg/m³"
        )
    return 0


def comando_versao(args: argparse.Namespace) -> int:
    """Exibe versão da ferramenta."""
    print(f"dosagem-concreto {__version__} · Lofrano Tecnologia")
    return 0


def criar_parser() -> argparse.ArgumentParser:
    """Constrói o analisador de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        prog="dosagem-concreto",
        description="Dosagem experimental e analítica de concreto pelo Método ABCP/ACI (ABNT NBR 12655 e NBR 6118).",
    )
    subparsers = parser.add_subparsers(dest="subcomando", help="Subcomando a executar")

    # Subcomando calcular
    parser_calc = subparsers.add_parser("calcular", help="Calcula a dosagem completa a partir de arquivo JSON")
    parser_calc.add_argument("arquivo_entrada", help="Caminho do arquivo JSON de parâmetros")
    parser_calc.add_argument("--saida-json", help="Caminho para salvar o resultado em JSON canônico")
    parser_calc.add_argument("--saida-md", help="Caminho para salvar o memorial em Markdown")
    parser_calc.add_argument("--saida-csv", help="Caminho para salvar a planilha CSV")
    parser_calc.add_argument("--saida-svg", help="Caminho para salvar o painel visual SVG")
    parser_calc.add_argument("--saida-zip", help="Caminho para salvar o pacote determinístico ZIP")
    parser_calc.add_argument("--sobrescrever", action="store_true", help="Permite sobrescrever arquivos existentes")
    parser_calc.set_defaults(func=comando_calcular)

    # Subcomando modelo
    parser_mod = subparsers.add_parser("modelo", help="Gera arquivo JSON com modelo de entrada")
    parser_mod.add_argument("--saida", "-o", help="Caminho do arquivo de saída (padrão: stdout)")
    parser_mod.set_defaults(func=comando_modelo)

    # Subcomando tabelas
    parser_tab = subparsers.add_parser("tabelas", help="Exibe tabelas de referência ABCP/NBR")
    parser_tab.set_defaults(func=comando_tabelas)

    # Subcomando versao
    parser_ver = subparsers.add_parser("versao", help="Exibe versão da ferramenta")
    parser_ver.set_defaults(func=comando_versao)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    parser = criar_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
