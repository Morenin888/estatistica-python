import argparse
import csv
import io
import math
import sys
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

LinhaDiscreta = namedtuple("LinhaDiscreta", "valor frequencia acumulada")
DistribuicaoClasses = namedtuple("DistribuicaoClasses",
    "classes n quantidade_classes amplitude_total amplitude_classe valor_constante quantidade_classes_sturges",
    defaults=(None, None))

class Classe(namedtuple("Classe", "limite_inferior limite_superior frequencia acumulada")):
    __slots__ = ()

    @property
    def ponto_medio(self):
        return _meio(self.limite_inferior, self.limite_superior)

class ErroEntrada(ValueError):
    pass

def validar_numero(valor, nome="Valor"):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nome} deve ser um número real.")
    try:
        numero = float(valor)
    except (OverflowError, ValueError) as erro:
        raise ValueError(f"{nome} excede o intervalo numérico suportado.") from erro
    if not math.isfinite(numero):
        raise ValueError(f"{nome} deve ser finito: NaN e infinito não são aceitos.")
    return numero

def validar_dados(dados):
    try:
        valores = [validar_numero(v, f"Observação {i}") for i, v in enumerate(dados, 1)]
    except TypeError as erro:
        raise ValueError("Os dados devem ser uma sequência de números.") from erro
    if not valores:
        raise ValueError("O conjunto de dados não pode estar vazio.")
    return valores

def validar_frequencia(valor, permitir_zero=False):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < (0 if permitir_zero else 1):
        raise ValueError("A frequência deve ser um inteiro positivo, ou zero nas classes.")
    return valor

def _meio(a, b):
    return (a + b) / 2 if a <= 0 <= b else a + (b - a) / 2

def _media_ponderada(valores, frequencias):
    escala, n = max(map(abs, valores)), sum(frequencias)
    if escala == 0:
        return 0.0
    soma = math.fsum((v / escala) * (f / n) for v, f in zip(valores, frequencias))
    return max(-1.0, min(1.0, soma)) * escala

def analisar_nao_agrupados(dados):
    import statistics
    return SimpleNamespace(media=statistics.mean(dados), mediana=statistics.median(dados),
                           moda=statistics.mode(dados))

def construir_tabela_discreta(dados):
    frequencias, tabela, acumulada = {}, [], 0
    for valor in validar_dados(dados):
        frequencias[valor] = frequencias.get(valor, 0) + 1
    for valor, fi in sorted(frequencias.items()):
        acumulada += fi
        tabela.append(LinhaDiscreta(valor, fi, acumulada))
    return tabela

def validar_tabela_discreta(tabela):
    linhas, anterior, acumulada = list(tabela), -math.inf, 0
    if not linhas:
        raise ValueError("A tabela de frequências não pode estar vazia.")
    for linha in linhas:
        valor = validar_numero(linha.valor)
        acumulada += validar_frequencia(linha.frequencia)
        if valor <= anterior or validar_frequencia(linha.acumulada) != acumulada:
            raise ValueError("Valores devem ser distintos e crescentes, com acumuladas corretas.")
        anterior = valor
    return linhas

def calcular_medidas_discretas(tabela):
    linhas = validar_tabela_discreta(tabela)
    n, maxima = linhas[-1].acumulada, max(l.frequencia for l in linhas)
    centrais = [next(l.valor for l in linhas if l.acumulada >= p) for p in ((n + 1) // 2, n // 2 + 1)]
    modas = [l.valor for l in linhas if l.frequencia == maxima]
    observacao = ""
    if len(modas) > 1:
        observacao = "Todos ocorrem uma vez: não há moda predominante." if maxima == 1 else "Há empate: todas as modas foram exibidas."
    return SimpleNamespace(media=_media_ponderada([l.valor for l in linhas], [l.frequencia for l in linhas]),
                           mediana=_meio(*centrais), modas=modas, observacao_moda=observacao)

def criar_distribuicao_manual(limites, frequencias, sturges=None):
    limites = [validar_numero(v, "Limite de classe") for v in limites]
    frequencias = [validar_frequencia(f, True) for f in frequencias]
    if not frequencias or len(limites) != len(frequencias) + 1:
        raise ValueError("Informe k frequências e k + 1 limites.")
    n, acumulada, classes = sum(frequencias), 0, []
    amplitude = validar_numero(limites[-1] - limites[0], "Amplitude total")
    for i, fi in enumerate(frequencias):
        acumulada += fi
        classes.append(Classe(limites[i], limites[i + 1], fi, acumulada))
    constante = limites[0] if len(classes) == 1 and amplitude == 0 else None
    distribuicao = DistribuicaoClasses(classes, n, len(classes), amplitude,
                                      amplitude / len(classes), constante, sturges)
    _validar_distribuicao(distribuicao)
    return distribuicao

def construir_distribuicao(dados):
    valores = validar_dados(dados)
    n, minimo, maximo = len(valores), min(valores), max(valores)
    k = math.ceil(1 + 3.322 * math.log10(n))
    amplitude = validar_numero(maximo - minimo, "Amplitude total")
    if amplitude == 0:
        return criar_distribuicao_manual([minimo, maximo], [n], k)
    h = amplitude / k
    limites = [minimo + i * h for i in range(k)] + [maximo]
    if h <= 0 or any(a >= b for a, b in zip(limites, limites[1:])):
        raise ValueError("Limites de classes se repetem por falta de precisão numérica; reescalone os dados.")
    frequencias = [0] * k
    for valor in valores:
        indice = min(int((valor - minimo) / h), k - 1)
        while indice > 0 and valor < limites[indice]:
            indice -= 1
        while indice < k - 1 and valor >= limites[indice + 1]:
            indice += 1
        frequencias[indice] += 1
    return criar_distribuicao_manual(limites, frequencias, k)

def _validar_distribuicao(d):
    validar_numero(validar_frequencia(d.n), "Total n")
    if not d.classes or len(d.classes) != validar_frequencia(d.quantidade_classes):
        raise ValueError("Quantidade de classes incompatível com a tabela.")
    amplitude, h = validar_numero(d.amplitude_total), validar_numero(d.amplitude_classe)
    acumulada, anterior = 0, d.classes[0].limite_inferior
    for classe in d.classes:
        li, ls = validar_numero(classe.limite_inferior), validar_numero(classe.limite_superior)
        acumulada += validar_frequencia(classe.frequencia, True)
        if validar_frequencia(classe.acumulada, True) != acumulada or li != anterior:
            raise ValueError("Classes devem ser contíguas, ordenadas e ter acumuladas corretas.")
        if d.valor_constante is None:
            largura = validar_numero(ls - li, "Amplitude da classe")
            tolerancia = 2 * max(math.ulp(li), math.ulp(ls), math.ulp(h))
            if largura <= 0 or h <= 0 or not math.isclose(largura, h, rel_tol=1e-12, abs_tol=tolerancia):
                raise ValueError("As classes devem ter a mesma amplitude positiva.")
        anterior = ls
    if acumulada != d.n or not math.isclose(amplitude, anterior - d.classes[0].limite_inferior):
        raise ValueError("Total n ou amplitude incompatível com a tabela.")
    if d.valor_constante is not None:
        v = validar_numero(d.valor_constante)
        if len(d.classes) != 1 or d.classes[0].limite_inferior != v or anterior != v or amplitude != 0 or h != 0:
            raise ValueError("Dados constantes devem ter uma única classe [v,v].")

def _separatriz(d, p):
    if d.valor_constante is not None:
        return d.valor_constante
    if p in (0, 1):
        return d.classes[0].limite_inferior if p == 0 else d.classes[-1].limite_superior
    posicao, anterior = p * d.n, 0
    for classe in d.classes:
        if classe.frequencia and classe.acumulada >= posicao:
            return classe.limite_inferior + (posicao - anterior) / classe.frequencia * d.amplitude_classe
        anterior = classe.acumulada

def calcular_separatriz(distribuicao, proporcao):
    proporcao = validar_numero(proporcao)
    if not 0 <= proporcao <= 1:
        raise ValueError("A proporção deve estar entre 0 e 1.")
    _validar_distribuicao(distribuicao)
    return _separatriz(distribuicao, proporcao)

def _modas_czuber(d):
    frequencias = [c.frequencia for c in d.classes]
    maxima = max(frequencias)
    indices = [i for i, f in enumerate(frequencias) if f == maxima]
    if d.valor_constante is not None:
        return [d.valor_constante], "Dados constantes: moda exata.", indices
    if maxima == 1:
        return [], "Frequência máxima igual a 1: não há classe modal predominante.", indices
    if len(indices) == len(frequencias) > 1:
        return [], "Todas as classes têm a mesma frequência: a moda não é única.", indices
    modas, observacao = [], "Há empate: as estimativas não determinam uma moda única." if len(indices) > 1 else ""
    vizinhas = [0] + frequencias + [0]
    for i in indices:
        d1, d2 = maxima - vizinhas[i], maxima - vizinhas[i + 2]
        if d1 + d2 == 0:
            observacao += " No platô, d1 + d2 = 0 impede interpolação."
        else:
            moda = d.classes[i].limite_inferior + d1 / (d1 + d2) * d.amplitude_classe
            if moda not in modas:
                modas.append(moda)
    return modas, observacao, indices

def calcular_medidas_classes(d):
    _validar_distribuicao(d)
    modas, observacao, indices = _modas_czuber(d)
    grupos = ({"Q1": .25, "Q3": .75}, {"D2": .2, "D7": .7},
              {"P15": .15, "P22": .22, "P63": .63, "P70": .7})
    quartis, decis, percentis = [{nome: _separatriz(d, p) for nome, p in grupo.items()} for grupo in grupos]
    media = d.valor_constante if d.valor_constante is not None else _media_ponderada(
        [c.ponto_medio for c in d.classes], [c.frequencia for c in d.classes])
    return SimpleNamespace(media=media, mediana=_separatriz(d, .5), modas=modas, quartis=quartis,
                           decis=decis, percentis=percentis, observacao_moda=observacao, classes_modais=indices)

def _converter_numero(texto, contexto, decimal_virgula=False):
    valor = texto.strip().replace(",", ".") if decimal_virgula else texto.strip()
    if not valor:
        raise ErroEntrada(f"{contexto}: campo vazio; informe um número.")
    try:
        return validar_numero(float(valor), contexto)
    except (ValueError, OverflowError) as erro:
        raise ErroEntrada(f"{contexto}: {texto!r} não é um número finito válido.") from erro

def ler_dados_manuais(texto):
    if not texto.strip():
        raise ErroEntrada("Nenhum dado informado; digite pelo menos um número.")
    separador = ";" if ";" in texto else ","
    return [_converter_numero(v, f"Valor {i}", separador == ";") for i, v in enumerate(texto.split(separador), 1)]

def _delimitador(texto):
    amostra = texto[:65536]
    try:
        detector = csv.Sniffer()
        detector.preferred = [";", "\t", ","]
        return detector.sniff(amostra, delimiters=";\t,").delimiter
    except csv.Error:
        primeira = next((l for l in amostra.splitlines() if l.strip()), "")
        return ";" if ";" in primeira else "\t" if "\t" in primeira else ","

def ler_csv(caminho, coluna=None, cabecalho=False):
    try:
        texto = Path(caminho).read_text(encoding="utf-8-sig")
    except FileNotFoundError as erro:
        raise ErroEntrada(f"Arquivo não encontrado: {caminho}.") from erro
    except PermissionError as erro:
        raise ErroEntrada(f"Sem permissão para ler: {caminho}.") from erro
    except UnicodeError as erro:
        raise ErroEntrada("O arquivo deve estar codificado em UTF-8.") from erro
    except OSError as erro:
        raise ErroEntrada(f"Não foi possível ler {caminho}: {erro}.") from erro
    if not texto.strip():
        raise ErroEntrada("O arquivo está vazio.")
    indice, nome = None, None
    if coluna is not None:
        if isinstance(coluna, int) or str(coluna).strip().lstrip("+-").isdigit():
            indice = int(coluna) - 1
            if indice < 0:
                raise ErroEntrada("O índice da coluna deve ser um inteiro a partir de 1.")
        else:
            nome = str(coluna).strip()
            if not nome or not cabecalho:
                raise ErroEntrada("Informe um nome de coluna e use --cabecalho.")
    delimitador = _delimitador(texto)
    leitor = csv.reader(io.StringIO(texto, newline=""), delimiter=delimitador, strict=True)
    fisicas, dados, primeira, anterior = texto.splitlines(keepends=True), [], True, 0
    try:
        for registro in leitor:
            inicio, fim = anterior + 1, leitor.line_num
            anterior = fim
            if not "".join(fisicas[inicio - 1:fim]).strip():
                continue
            eh_cabecalho = primeira and cabecalho
            if eh_cabecalho and nome is not None:
                encontrados = [i for i, v in enumerate(registro) if v.strip() == nome]
                if len(encontrados) != 1:
                    motivo = "não encontrada" if not encontrados else "aparece mais de uma vez"
                    raise ErroEntrada(f"Linha {inicio}: coluna {nome!r} {motivo} no cabeçalho.")
                indice = encontrados[0]
            if indice is not None and indice >= len(registro):
                raise ErroEntrada(f"Linha {inicio}: coluna {indice + 1} não existe.")
            if not eh_cabecalho:
                celulas = enumerate(registro) if indice is None else [(indice, registro[indice])]
                dados.extend(_converter_numero(v, f"Linha {inicio}, coluna {i + 1}", delimitador != ",")
                             for i, v in celulas)
            primeira = False
    except csv.Error as erro:
        raise ErroEntrada(f"CSV inválido próximo à linha {leitor.line_num}: {erro}.") from erro
    if not dados:
        raise ErroEntrada("O arquivo não contém dados numéricos para analisar.")
    return dados

def _numero(valor):
    texto = f"{valor:.12g}"
    return "0" if texto == "-0" else texto

def _tabela(titulos, linhas):
    linhas = [titulos] + [[str(v) for v in linha] for linha in linhas]
    larguras = [max(len(v) for v in coluna) for coluna in zip(*linhas)]
    for linha in linhas:
        print(" | ".join(v.rjust(w) for v, w in zip(linha, larguras)))

def _exibir_medidas(titulo, resultado):
    modas = ", ".join(map(_numero, resultado.modas)) or "não definida"
    print(f"{titulo}: Média = {_numero(resultado.media)} | Mediana = {_numero(resultado.mediana)} | Moda(s) = {modas}")
    if resultado.observacao_moda:
        print(resultado.observacao_moda)

def exibir_analise(dados):
    dados = validar_dados(dados)
    primeira = analisar_nao_agrupados(dados)
    try:
        validar_dados([primeira.media, primeira.mediana, primeira.moda])
    except ValueError as erro:
        raise ValueError("statistics produziu um resultado não finito; use valores de menor magnitude.") from erro
    tabela = construir_tabela_discreta(dados)
    segunda, d = calcular_medidas_discretas(tabela), construir_distribuicao(dados)
    terceira = calcular_medidas_classes(d)
    print("\nPARTE 1: DADOS NÃO AGRUPADOS (Statistics)")
    for nome, valor in (("Média", primeira.media), ("Mediana", primeira.mediana), ("Moda", primeira.moda)):
        print(f"{nome}: {_numero(valor)}")
    if len(segunda.modas) > 1:
        print("statistics.mode retorna a primeira moda encontrada em caso de empate.")
    print("\nPARTE 2: DISTRIBUIÇÃO DE FREQUÊNCIA (SEM INTERVALO)")
    _tabela(["Valor (xi)", "Freq. Absoluta (fi)", "Freq. Acumulada (Fi)"],
            [[repr(l.valor), l.frequencia, l.acumulada] for l in tabela])
    _exibir_medidas("Via tabela discreta", segunda)
    print("\nPARTE 3: DISTRIBUIÇÃO DE FREQUÊNCIA (COM INTERVALO)")
    print(f"n = {d.n} | k = {d.quantidade_classes_sturges} (Sturges)")
    print(f"Amplitude total = {_numero(d.amplitude_total)} | Amplitude de classe (h) = {_numero(d.amplitude_classe)}")
    if d.valor_constante is not None:
        print("Dados constantes: Classes efetivas = 1; medidas exatas iguais ao valor observado.")
    _tabela(["Intervalo de Classe", "fi", "Fi", "Ponto médio"],
            [[f"[{c.limite_inferior!r} - {c.limite_superior!r}{']' if i == len(d.classes) - 1 else ')'}",
              c.frequencia, c.acumulada, _numero(c.ponto_medio)] for i, c in enumerate(d.classes)])
    _exibir_medidas("Via interpolação (Czuber), estimativas", terceira)
    for nome in ("quartis", "decis", "percentis"):
        print(f"{nome.title()}: " + " | ".join(f"{chave} = {_numero(v)}" for chave, v in getattr(terceira, nome).items()))

class _FormatoPortugues(argparse.HelpFormatter):
    def _format_usage(self, usage, actions, groups, prefix=None):
        return super()._format_usage(usage, actions, groups, prefix or "uso: ")

def criar_parser():
    parser = argparse.ArgumentParser(description="Analisador estatístico: três níveis de dados.", formatter_class=_FormatoPortugues)
    parser._optionals.title = "Opções"
    fonte = parser.add_mutually_exclusive_group()
    fonte.add_argument("--dados", help="números separados por vírgula (ponto decimal) ou ; (vírgula decimal)")
    fonte.add_argument("--csv", type=Path, help="arquivo CSV em UTF-8")
    parser.add_argument("--coluna", help="nome ou índice da coluna CSV a partir de 1")
    parser.add_argument("--cabecalho", action="store_true", help="pula o cabeçalho explícito do CSV")
    return parser

def _menu():
    while True:
        print("\nANALISADOR ESTATÍSTICO - ENGENHARIA DE SOFTWARE\n[1] Inserir dados\n[2] Carregar CSV\n[0] Sair")
        opcao = input("Escolha a opção: ").strip()
        if opcao == "0":
            print("Programa encerrado.")
            return 0
        if opcao not in ("1", "2"):
            print("Opção inválida. Escolha 1, 2 ou 0.")
            continue
        try:
            if opcao == "1":
                dados = ler_dados_manuais(input("Números (ex.: 1,2,3 ou 1,5;2,5): "))
            else:
                caminho = input("Caminho do arquivo CSV: ").strip()
                resposta = input("Possui cabeçalho? [s/N]: ").strip().lower()
                if resposta not in ("", "n", "nao", "não", "s", "sim"):
                    raise ErroEntrada("Resposta inválida; informe s ou n.")
                coluna = input("Coluna (nome ou índice; Enter para todas): ").strip()
                dados = ler_csv(caminho, coluna or None, resposta in ("s", "sim"))
            print(f"Dados carregados com sucesso! (n = {len(dados)} elementos)")
            exibir_analise(dados)
        except (ValueError, OverflowError) as erro:
            print(f"Erro: {erro}\nRetornando ao menu; verifique os dados.")

def main(argv=None):
    parser = criar_parser()
    args = parser.parse_args(argv)
    if args.csv is None and (args.coluna is not None or args.cabecalho):
        parser.error("--coluna e --cabecalho só podem ser usados com --csv")
    try:
        if args.dados is None and args.csv is None:
            return _menu()
        dados = ler_dados_manuais(args.dados) if args.dados is not None else ler_csv(args.csv, args.coluna, args.cabecalho)
        print(f"Dados carregados com sucesso! (n = {len(dados)} elementos)")
        exibir_analise(dados)
        return 0
    except (ValueError, OverflowError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nPrograma encerrado.")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
