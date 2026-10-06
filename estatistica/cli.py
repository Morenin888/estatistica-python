"""Interface de linha de comando do analisador estatístico."""

import argparse
from pathlib import Path
import sys

from . import (
    analisar_nao_agrupados,
    calcular_medidas_classes,
    calcular_medidas_discretas,
    construir_distribuicao,
    construir_tabela_discreta,
    validar_dados,
)
from .entrada import ErroEntrada, ler_csv, ler_dados_manuais


class _FormatoPortugues(argparse.HelpFormatter):
    def _format_usage(self, usage, actions, groups, prefix=None):
        return super()._format_usage(usage, actions, groups, prefix or "uso: ")


class _ParserPortugues(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: erro: {message}\n")


def criar_parser() -> argparse.ArgumentParser:
    parser = _ParserPortugues(
        description="Analisa dados nas três etapas do trabalho de Probabilidade e Estatística.",
        epilog=(
            "Sem --dados ou --csv, abre o menu interativo. Para números negativos, "
            "use --dados=-2,-1,0. Cabeçalhos CSV só são pulados com --cabecalho."
        ),
        formatter_class=_FormatoPortugues,
        add_help=False,
    )
    parser._optionals.title = "Opções"
    parser.add_argument("-h", "--help", action="help", help="mostra esta ajuda e encerra")
    fonte = parser.add_mutually_exclusive_group()
    fonte.add_argument(
        "--dados", metavar="NÚMEROS",
        help="dados separados por vírgula (decimal com ponto), ou ; (decimal com vírgula)",
    )
    fonte.add_argument("--csv", type=Path, metavar="ARQUIVO", help="caminho de um arquivo CSV em UTF-8")
    parser.add_argument(
        "--coluna", metavar="NOME_OU_ÍNDICE",
        help="seleciona uma coluna CSV por índice a partir de 1 ou por nome do cabeçalho",
    )
    parser.add_argument(
        "--cabecalho", action="store_true",
        help="considera a primeira linha não vazia do CSV como cabeçalho",
    )
    return parser


def _numero(valor: float) -> str:
    texto = f"{valor:.12g}"
    return "0" if texto == "-0" else texto


def _numero_exato(valor: float) -> str:
    texto = repr(valor)
    return texto[:-2] if texto.endswith(".0") else texto


def _modas(valores: list[float]) -> str:
    return ", ".join(_numero(valor) for valor in valores) if valores else "não definida"


def _titulo(texto: str) -> None:
    print("\n" + "-" * 72)
    print(texto)
    print("-" * 72)


def exibir_analise(dados: list[float]) -> None:
    """Calcula e apresenta as três partes usando seus módulos independentes."""
    dados = validar_dados(dados)
    primeira = analisar_nao_agrupados(dados)
    try:
        validar_dados([primeira.media, primeira.mediana, primeira.moda])
    except ValueError as exc:
        raise ValueError(
            "O módulo statistics produziu um resultado não finito; use valores de menor magnitude."
        ) from exc
    tabela = construir_tabela_discreta(dados)
    segunda = calcular_medidas_discretas(tabela)
    distribuicao = construir_distribuicao(dados)
    terceira = calcular_medidas_classes(distribuicao)

    _titulo("PARTE 1: DADOS NÃO AGRUPADOS (Módulo Statistics)")
    print(f"Média: {_numero(primeira.media)}")
    print(f"Mediana: {_numero(primeira.mediana)}")
    print(f"Moda: {_numero(primeira.moda)}")
    if len(segunda.modas) > 1:
        print("Nota: statistics.mode retorna a primeira moda encontrada em caso de empate.")

    _titulo("PARTE 2: DISTRIBUIÇÃO DE FREQUÊNCIA (SEM INTERVALO)")
    print(f"{'Valor (xi)':>16} | {'Freq. Absoluta (fi)':>20} | {'Freq. Acumulada (Fi)':>21}")
    formatar_valor = _numero_exato if len({_numero(linha.valor) for linha in tabela}) < len(tabela) else _numero
    for linha in tabela:
        print(f"{formatar_valor(linha.valor):>16} | {linha.frequencia:>20} | {linha.acumulada:>21}")
    print(
        "Calculados via tabela: "
        f"Média = {_numero(segunda.media)} | Mediana = {_numero(segunda.mediana)} | "
        f"Moda(s) = {_modas(segunda.modas)}"
    )
    if segunda.observacao_moda:
        print(f"Nota: {segunda.observacao_moda}")

    _titulo("PARTE 3: DISTRIBUIÇÃO DE FREQUÊNCIA (COM INTERVALO)")
    print(f"n = {distribuicao.n} | k = {distribuicao.quantidade_classes_sturges} (Sturges)")
    if distribuicao.valor_constante is not None:
        print(f"Classes efetivas = {distribuicao.quantidade_classes} (dados constantes)")
    print(
        f"Amplitude total = {_numero(distribuicao.amplitude_total)} | "
        f"Amplitude de classe (h) = {_numero(distribuicao.amplitude_classe)}"
    )
    print(f"{'Intervalo de Classe':>30} | {'fi':>6} | {'Fi':>6} | {'Ponto médio':>12}")
    for indice, classe in enumerate(distribuicao.classes):
        fechamento = "]" if indice == len(distribuicao.classes) - 1 else ")"
        limite_inferior = _numero(classe.limite_inferior)
        limite_superior = _numero(classe.limite_superior)
        if classe.limite_inferior != classe.limite_superior and limite_inferior == limite_superior:
            limite_inferior = _numero_exato(classe.limite_inferior)
            limite_superior = _numero_exato(classe.limite_superior)
        intervalo = (
            f"[{limite_inferior} - {limite_superior}{fechamento}"
        )
        print(
            f"{intervalo:>30} | {classe.frequencia:>6} | {classe.acumulada:>6} | "
            f"{_numero(classe.ponto_medio):>12}"
        )
    if distribuicao.valor_constante is not None:
        print("Dados constantes: uma única classe de amplitude zero; medidas iguais ao valor observado.")
    print("Calculados via fórmulas clássicas; medidas agrupadas são estimativas:")
    print(
        f"-> Média: {_numero(terceira.media)} | Mediana: {_numero(terceira.mediana)} | "
        f"Moda(s), método de Czuber: {_modas(terceira.modas)}"
    )
    if terceira.observacao_moda:
        print(f"Nota: {terceira.observacao_moda}")
    for titulo, medidas in (
        ("Quartis", terceira.quartis),
        ("Decis", terceira.decis),
        ("Percentis", terceira.percentis),
    ):
        print(f"-> {titulo}: " + " | ".join(f"{nome} = {_numero(valor)}" for nome, valor in medidas.items()))


def _menu() -> int:
    while True:
        print("\n" + "=" * 72)
        print("ANALISADOR ESTATÍSTICO - ENGENHARIA DE SOFTWARE")
        print("=" * 72)
        print("[1] Inserir dados via terminal (separados por vírgula)")
        print("[2] Carregar arquivo .csv")
        print("[0] Sair")
        opcao = input("Escolha a opção: ").strip()
        if opcao == "0":
            print("Programa encerrado.")
            return 0
        if opcao not in ("1", "2"):
            print("Opção inválida. Escolha 1, 2 ou 0.")
            continue
        try:
            if opcao == "1":
                texto = input("Digite os números (ex.: 1,2,3 ou 1,5;2,5;3,5): ")
                dados = ler_dados_manuais(texto)
            else:
                caminho = input("Caminho do arquivo CSV: ").strip()
                if not caminho:
                    raise ErroEntrada("Informe o caminho do arquivo CSV.")
                resposta = input("O CSV possui cabeçalho? [s/N]: ").strip().lower()
                if resposta not in ("", "n", "nao", "não", "s", "sim"):
                    raise ErroEntrada("Resposta de cabeçalho inválida; informe s ou n.")
                coluna = input("Coluna (nome ou índice a partir de 1; Enter para todas): ").strip()
                dados = ler_csv(caminho, coluna=coluna or None, cabecalho=resposta in ("s", "sim"))
            print(f"Dados carregados com sucesso! (n = {len(dados)} elementos)")
            exibir_analise(dados)
        except (ErroEntrada, ValueError, OverflowError) as exc:
            print(f"Erro: {exc}")
            print("Retornando ao menu; verifique os dados e tente novamente.")


def main(argv: list[str] | None = None) -> int:
    parser = criar_parser()
    args = parser.parse_args(argv)
    if args.csv is None and (args.coluna is not None or args.cabecalho):
        parser.error("--coluna e --cabecalho só podem ser usados com --csv")
    try:
        if args.dados is None and args.csv is None:
            return _menu()
        dados = (
            ler_dados_manuais(args.dados)
            if args.dados is not None
            else ler_csv(args.csv, coluna=args.coluna, cabecalho=args.cabecalho)
        )
        print(f"Dados carregados com sucesso! (n = {len(dados)} elementos)")
        exibir_analise(dados)
        return 0
    except (ErroEntrada, ValueError, OverflowError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nPrograma encerrado.")
        return 0
