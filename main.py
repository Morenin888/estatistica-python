"""Analisador estatístico descritivo — aplicação completa em um único arquivo.

Requer Python 3.10 ou superior e usa somente a biblioteca padrão.
A organização por funções e classes mantém independentes a validação,
os cálculos de cada parte, a leitura dos dados e a interface do terminal.
Execute: python main.py --help
"""

import argparse
import csv
import io
import math
import sys
from dataclasses import dataclass
from pathlib import Path



# ============================================================================
# VALIDAÇÃO DE DADOS E TABELAS
# ============================================================================

def validar_numero(valor, nome="Valor"):
    """Aceita números reais finitos e devolve um float, sem aceitar booleanos."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nome} deve ser um número real.")
    try:
        numero = float(valor)
    except (OverflowError, ValueError) as erro:
        raise ValueError(f"{nome} está fora do intervalo numérico suportado.") from erro
    if not math.isfinite(numero):
        raise ValueError(f"{nome} deve ser finito: NaN e infinito não são aceitos.")
    return numero


def validar_dados(dados):
    """Valida uma sequência não vazia de observações numéricas."""
    try:
        iterador = iter(dados)
    except TypeError as erro:
        raise ValueError("Os dados devem ser uma sequência de números.") from erro
    resultado = [validar_numero(valor, f"Observação {i}")
                 for i, valor in enumerate(iterador, start=1)]
    if not resultado:
        raise ValueError("O conjunto de dados não pode estar vazio.")
    return resultado


def validar_frequencia(valor, nome="Frequência", permitir_zero=False):
    """Frequências e totais são inteiros; não arredonda valores inválidos."""
    minimo = 0 if permitir_zero else 1
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < minimo:
        raise ValueError(f"{nome} deve ser um inteiro maior ou igual a {minimo}.")
    return valor


def validar_tabela_discreta(tabela):
    """Confere ordem, frequências e acumuladas de uma tabela discreta."""
    linhas = list(tabela)
    if not linhas:
        raise ValueError("A tabela de frequências não pode estar vazia.")
    anterior = None
    acumulada = 0
    for i, linha in enumerate(linhas, start=1):
        try:
            valor = validar_numero(linha.valor, f"Valor da linha {i}")
            frequencia = validar_frequencia(linha.frequencia)
            validar_frequencia(linha.acumulada, "Frequência acumulada")
        except AttributeError as erro:
            raise ValueError("Cada linha deve conter valor, frequência e acumulada.") from erro
        if anterior is not None and valor <= anterior:
            raise ValueError("Os valores da tabela devem ser distintos e crescentes.")
        acumulada += frequencia
        if linha.acumulada != acumulada:
            raise ValueError("A frequência acumulada não corresponde à soma das frequências.")
        anterior = valor
    return linhas


# ============================================================================
# PARTE 1: DADOS NÃO AGRUPADOS — PACOTE STATISTICS
# ============================================================================

class ResultadoNaoAgrupados:
    """Resultado das três funções nativas do pacote statistics."""

    def __init__(self, media, mediana, moda):
        self.media = media
        self.mediana = mediana
        self.moda = moda


def analisar_nao_agrupados(dados):
    """Aplica mean, median e mode diretamente aos dados já validados."""
    import statistics

    return ResultadoNaoAgrupados(
        media=statistics.mean(dados),
        mediana=statistics.median(dados),
        moda=statistics.mode(dados),
    )


# ============================================================================
# PARTE 2: DISTRIBUIÇÃO DISCRETA — CÁLCULO PELA TABELA
# ============================================================================

@dataclass(frozen=True)
class LinhaDiscreta:
    valor: float
    frequencia: int
    acumulada: int


@dataclass(frozen=True)
class ResultadoDiscretos:
    media: float
    mediana: float
    modas: list[float]
    observacao_moda: str = ""


def construir_tabela_discreta(dados):
    """Conta valores em um dicionário e ordena xi, fi e Fi."""
    frequencias = {}
    for valor in validar_dados(dados):
        frequencias[valor] = frequencias.get(valor, 0) + 1
    tabela = []
    acumulada = 0
    for valor in sorted(frequencias):
        acumulada += frequencias[valor]
        tabela.append(LinhaDiscreta(valor, frequencias[valor], acumulada))
    return tabela


def _valor_na_posicao(tabela, posicao):
    """Encontra uma posição ordinal, começando em 1, pela coluna Fi."""
    for linha in tabela:
        if linha.acumulada >= posicao:
            return linha.valor
    raise ValueError("Posição fora da tabela de frequências.")


def calcular_medidas_discretas(tabela):
    """Calcula média ponderada, mediana pelas acumuladas e todas as modas."""
    linhas = validar_tabela_discreta(tabela)
    n = linhas[-1].acumulada
    # A escala é algebraicamente neutra e evita overflow em xi * fi.
    escala = max(abs(linha.valor) for linha in linhas)
    if escala == 0:
        media = 0.0
    else:
        media_normalizada = math.fsum(
            (linha.valor / escala) * (linha.frequencia / n) for linha in linhas
        )
        media = max(-1.0, min(1.0, media_normalizada)) * escala
    if n % 2:
        mediana = _valor_na_posicao(linhas, n // 2 + 1)
    else:
        inferior = _valor_na_posicao(linhas, n // 2)
        superior = _valor_na_posicao(linhas, n // 2 + 1)
        # Com sinais opostos a soma não estoura; com sinais iguais a
        # diferença não estoura e evita dividir duas subnormais separadamente.
        mediana = ((inferior + superior) / 2 if inferior <= 0 <= superior
                   else inferior + (superior - inferior) / 2)
    frequencia_maxima = max(linha.frequencia for linha in linhas)
    modas = [linha.valor for linha in linhas if linha.frequencia == frequencia_maxima]
    if frequencia_maxima == 1 and len(linhas) > 1:
        observacao = ("Todos os valores ocorrem uma vez: não há moda predominante; "
                      "a lista mostra todos os valores empatados.")
    elif len(modas) > 1:
        observacao = "Há empate na frequência máxima: todas as modas foram exibidas."
    else:
        observacao = ""
    return ResultadoDiscretos(media, mediana, modas, observacao)


# ============================================================================
# PARTE 3: INTERVALOS DE CLASSE — FÓRMULAS CLÁSSICAS
# ============================================================================

@dataclass(frozen=True)
class Classe:
    limite_inferior: float
    limite_superior: float
    frequencia: int
    acumulada: int

    @property
    def ponto_medio(self):
        li, ls = self.limite_inferior, self.limite_superior
        return (li + ls) / 2 if li <= 0 <= ls else li + (ls - li) / 2


@dataclass(frozen=True)
class DistribuicaoClasses:
    classes: list[Classe]
    n: int
    quantidade_classes: int
    amplitude_total: float
    amplitude_classe: float
    valor_constante: float | None = None
    quantidade_classes_sturges: int | None = None


@dataclass(frozen=True)
class ResultadoClasses:
    media: float
    mediana: float
    modas: list[float]
    quartis: dict[str, float]
    decis: dict[str, float]
    percentis: dict[str, float]
    observacao_moda: str = ""
    classes_modais: list[int] | None = None


def _classes_com_acumuladas(limites, frequencias):
    acumulada = 0
    classes = []
    for i, frequencia in enumerate(frequencias):
        acumulada += frequencia
        classes.append(Classe(limites[i], limites[i + 1], frequencia, acumulada))
    return classes


def construir_distribuicao(dados):
    """Constrói [Li,Ls), com último intervalo fechado, pela regra de Sturges."""
    valores = validar_dados(dados)
    n = len(valores)
    k = math.ceil(1 + 3.322 * math.log10(n))
    minimo, maximo = min(valores), max(valores)
    amplitude = maximo - minimo
    if not math.isfinite(amplitude):
        raise ValueError("A amplitude total excede o intervalo numérico suportado.")
    if amplitude == 0:
        return DistribuicaoClasses(
            [Classe(minimo, maximo, n, n)], n, 1, 0.0, 0.0, minimo, k
        )
    h = amplitude / k
    if h <= 0 or not math.isfinite(h):
        raise ValueError("A amplitude das classes não pode ser representada numericamente.")
    limites = [minimo + i * h for i in range(k)] + [maximo]
    if any(limites[i] >= limites[i + 1] for i in range(k)):
        raise ValueError("Limites de classes se repetem por falta de precisão numérica; "
                         "reescalone os dados para construir os intervalos.")
    frequencias = [0] * k
    for valor in valores:
        if valor == maximo:
            indice = k - 1
        else:
            indice = min(int((valor - minimo) / h), k - 1)
            # Corrige o quociente usando os limites efetivamente armazenados.
            # Não há tolerância que desloque observações reais perto da fronteira.
            while indice > 0 and valor < limites[indice]:
                indice -= 1
            while indice < k - 1 and valor >= limites[indice + 1]:
                indice += 1
        frequencias[indice] += 1
    classes = _classes_com_acumuladas(limites, frequencias)
    return DistribuicaoClasses(classes, n, k, amplitude, h, None, k)


def criar_distribuicao_manual(limites, frequencias):
    """Permite conferir as fórmulas com tabelas clássicas de classes iguais."""
    limites = [validar_numero(valor, "Limite de classe") for valor in limites]
    frequencias = [validar_frequencia(fi, permitir_zero=True) for fi in frequencias]
    if not frequencias or len(limites) != len(frequencias) + 1:
        raise ValueError("Informe k frequências e k + 1 limites de classes.")
    n = sum(frequencias)
    if n == 0:
        raise ValueError("A soma das frequências deve ser positiva.")
    amplitude = limites[-1] - limites[0]
    if not math.isfinite(amplitude):
        raise ValueError("A amplitude total excede o intervalo numérico suportado.")
    constante = limites[0] if len(frequencias) == 1 and amplitude == 0 else None
    distribuicao = DistribuicaoClasses(
        _classes_com_acumuladas(limites, frequencias), n, len(frequencias),
        amplitude, amplitude / len(frequencias), constante
    )
    _validar_distribuicao(distribuicao)
    return distribuicao


def _validar_distribuicao(distribuicao):
    classes = distribuicao.classes
    validar_frequencia(distribuicao.n, "Total n")
    validar_numero(distribuicao.n, "Total n")
    validar_frequencia(distribuicao.quantidade_classes, "Quantidade de classes")
    if not classes or len(classes) != distribuicao.quantidade_classes:
        raise ValueError("A quantidade de classes não corresponde à tabela.")
    amplitude = validar_numero(distribuicao.amplitude_total, "Amplitude total")
    h = validar_numero(distribuicao.amplitude_classe, "Amplitude de classe")
    acumulada = 0
    for i, classe in enumerate(classes):
        li = validar_numero(classe.limite_inferior, "Limite inferior")
        ls = validar_numero(classe.limite_superior, "Limite superior")
        acumulada += validar_frequencia(classe.frequencia, permitir_zero=True)
        validar_frequencia(classe.acumulada, "Frequência acumulada", permitir_zero=True)
        if classe.acumulada != acumulada:
            raise ValueError("Frequência acumulada incompatível com a tabela de classes.")
        if i and li != classes[i - 1].limite_superior:
            raise ValueError("As classes devem ser contíguas e ordenadas.")
        if distribuicao.valor_constante is None:
            largura = ls - li
            if not math.isfinite(largura) or largura <= 0 or h <= 0:
                raise ValueError("As classes devem possuir amplitude positiva e finita.")
            tolerancia = max(math.ulp(li), math.ulp(ls), math.ulp(h)) * 2
            if not math.isclose(largura, h, rel_tol=1e-12, abs_tol=tolerancia):
                raise ValueError("A interpolação exige classes de mesma amplitude.")
    if acumulada != distribuicao.n:
        raise ValueError("O total n não corresponde à soma das frequências.")
    amplitude_real = classes[-1].limite_superior - classes[0].limite_inferior
    if not math.isfinite(amplitude_real) or not math.isclose(amplitude, amplitude_real):
        raise ValueError("A amplitude total não corresponde aos limites da tabela.")
    if distribuicao.valor_constante is not None:
        valor = validar_numero(distribuicao.valor_constante, "Valor constante")
        if (len(classes) != 1 or classes[0].limite_inferior != valor
                or classes[0].limite_superior != valor or amplitude != 0 or h != 0):
            raise ValueError("Uma distribuição constante deve ter uma única classe [v,v].")


def _separatriz_validada(distribuicao, proporcao):
    if distribuicao.valor_constante is not None:
        return distribuicao.valor_constante
    if proporcao == 0:
        return distribuicao.classes[0].limite_inferior
    if proporcao == 1:
        return distribuicao.classes[-1].limite_superior
    posicao = proporcao * distribuicao.n
    anterior = 0
    for classe in distribuicao.classes:
        if classe.frequencia > 0 and classe.acumulada >= posicao:
            fracao = (posicao - anterior) / classe.frequencia
            return classe.limite_inferior + fracao * distribuicao.amplitude_classe
        anterior = classe.acumulada
    raise ValueError("A posição solicitada não foi encontrada na tabela.")


def calcular_separatriz(distribuicao, proporcao):
    """Usa L + ((p*n - F_anterior)/fi) * h; p deve estar entre 0 e 1."""
    proporcao = validar_numero(proporcao, "Proporção")
    if not 0 <= proporcao <= 1:
        raise ValueError("A proporção deve estar entre 0 e 1.")
    _validar_distribuicao(distribuicao)
    return _separatriz_validada(distribuicao, proporcao)


def _modas_czuber(distribuicao):
    classes = distribuicao.classes
    maxima = max(classe.frequencia for classe in classes)
    indices = [i for i, classe in enumerate(classes) if classe.frequencia == maxima]
    if distribuicao.valor_constante is not None:
        return [distribuicao.valor_constante], "Dados constantes: moda exata.", indices
    if maxima == 1:
        return [], "Frequência máxima igual a 1: não há classe modal predominante.", indices
    if len(indices) == len(classes) and len(classes) > 1:
        return [], "Todas as classes têm a mesma frequência: a moda não é única.", indices
    modas = []
    sem_interpolacao = False
    for i in indices:
        anterior = classes[i - 1].frequencia if i > 0 else 0
        seguinte = classes[i + 1].frequencia if i + 1 < len(classes) else 0
        d1, d2 = maxima - anterior, maxima - seguinte
        if d1 + d2 == 0:
            sem_interpolacao = True
            continue
        moda = classes[i].limite_inferior + d1 / (d1 + d2) * distribuicao.amplitude_classe
        if moda not in modas:
            modas.append(moda)
    observacao = ""
    if len(indices) > 1:
        observacao = ("Há empate entre classes modais; as estimativas de Czuber "
                      "não determinam uma moda única.")
    if sem_interpolacao:
        observacao += " Em trecho de frequência constante, d1 + d2 = 0 impede interpolação."
    return modas, observacao, indices


def calcular_medidas_classes(distribuicao):
    """Obtém média por pontos médios, Czuber e as separatrizes solicitadas."""
    _validar_distribuicao(distribuicao)
    if distribuicao.valor_constante is not None:
        media = distribuicao.valor_constante
    else:
        escala = max(abs(classe.ponto_medio) for classe in distribuicao.classes)
        media = 0.0 if escala == 0 else max(-1.0, min(1.0, math.fsum(
            (classe.ponto_medio / escala) * (classe.frequencia / distribuicao.n)
            for classe in distribuicao.classes
        ))) * escala
    modas, observacao, indices = _modas_czuber(distribuicao)
    quartis = {nome: _separatriz_validada(distribuicao, p)
               for nome, p in (("Q1", 0.25), ("Q3", 0.75))}
    decis = {nome: _separatriz_validada(distribuicao, p)
             for nome, p in (("D2", 0.2), ("D7", 0.7))}
    percentis = {nome: _separatriz_validada(distribuicao, p)
                for nome, p in (("P15", 0.15), ("P22", 0.22), ("P63", 0.63), ("P70", 0.7))}
    return ResultadoClasses(media, _separatriz_validada(distribuicao, 0.5),
                            modas, quartis, decis, percentis, observacao, indices)


# ============================================================================
# ENTRADA MANUAL E LEITURA DE CSV
# ============================================================================

class ErroEntrada(ValueError):
    """Um dado informado não pode ser processado como número finito."""


def _converter_numero(texto: str, contexto: str, decimal_virgula: bool = False) -> float:
    valor = texto.strip()
    if not valor:
        raise ErroEntrada(f"{contexto}: campo vazio; informe um número.")
    if decimal_virgula:
        valor = valor.replace(",", ".")
    try:
        numero = float(valor)
    except (ValueError, OverflowError) as exc:
        raise ErroEntrada(f"{contexto}: {texto!r} não é um número válido.") from exc
    if not math.isfinite(numero):
        raise ErroEntrada(f"{contexto}: {texto!r} não é um número finito (NaN/inf).")
    return numero


def ler_dados_manuais(texto: str) -> list[float]:
    """Aceita vírgula entre números com ponto decimal, ou ; com vírgula decimal."""
    if not texto.strip():
        raise ErroEntrada("Nenhum dado informado; digite pelo menos um número.")
    separador = ";" if ";" in texto else ","
    return [
        _converter_numero(valor, f"Valor {indice}", decimal_virgula=separador == ";")
        for indice, valor in enumerate(texto.split(separador), start=1)
    ]


def _delimitador(texto: str) -> str:
    """Prioriza ;/tab para que uma vírgula decimal não vire um separador."""
    amostra = texto[:65536]
    try:
        detector = csv.Sniffer()
        detector.preferred = [";", "\t", ","]
        return detector.sniff(amostra, delimiters=";\t,").delimiter
    except csv.Error:
        # Arquivos de uma coluna podem não ter separador. Em arquivos irregulares,
        # a validação posterior deve apontar a célula problemática sem descartá-la.
        linhas = [linha for linha in amostra.splitlines() if linha.strip()]
        primeira = linhas[0] if linhas else ""
        if ";" in primeira:
            return ";"
        if "\t" in primeira:
            return "\t"
        return ","


def ler_csv(
    caminho: str | Path,
    coluna: str | int | None = None,
    cabecalho: bool = False,
) -> list[float]:
    """Lê todas as células numéricas ou uma coluna (nome ou índice a partir de 1).

    Cabeçalhos nunca são inferidos: devem ser solicitados explicitamente.
    Só linhas fisicamente vazias são ignoradas; campos vazios são erros.
    """
    arquivo = Path(caminho)
    try:
        texto = arquivo.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ErroEntrada(f"Arquivo não encontrado: {arquivo}.") from exc
    except PermissionError as exc:
        raise ErroEntrada(f"Sem permissão para ler o arquivo: {arquivo}.") from exc
    except UnicodeError as exc:
        raise ErroEntrada(f"O arquivo {arquivo} deve estar codificado em UTF-8.") from exc
    except OSError as exc:
        raise ErroEntrada(f"Não foi possível ler {arquivo}: {exc}.") from exc

    if not texto.strip():
        raise ErroEntrada(f"O arquivo {arquivo} está vazio.")
    delimitador = _delimitador(texto)
    linhas_fisicas = texto.splitlines(keepends=True)
    leitor = csv.reader(io.StringIO(texto, newline=""), delimiter=delimitador, strict=True)
    dados: list[float] = []
    indice_coluna: int | None = None
    nome_coluna: str | None = None
    if coluna is not None:
        if isinstance(coluna, int) or str(coluna).strip().lstrip("+-").isdigit():
            indice_coluna = int(coluna) - 1
            if indice_coluna < 0:
                raise ErroEntrada("O índice de --coluna deve ser um inteiro a partir de 1.")
        else:
            nome_coluna = str(coluna).strip()
            if not nome_coluna:
                raise ErroEntrada("O nome de --coluna não pode estar vazio.")
            if not cabecalho:
                raise ErroEntrada("Para selecionar uma coluna por nome, use --cabecalho.")

    primeira_linha = True
    linha_anterior = 0
    try:
        for registro in leitor:
            inicio_linha = linha_anterior + 1
            fim_linha = leitor.line_num
            linha_anterior = fim_linha
            original = "".join(linhas_fisicas[inicio_linha - 1 : fim_linha])
            if not original.strip():
                continue
            if primeira_linha and cabecalho:
                primeira_linha = False
                nomes = [valor.strip() for valor in registro]
                if nome_coluna is not None:
                    ocorrencias = [i for i, nome in enumerate(nomes) if nome == nome_coluna]
                    if not ocorrencias:
                        raise ErroEntrada(
                            f"Linha {inicio_linha}: coluna {nome_coluna!r} não encontrada no cabeçalho."
                        )
                    if len(ocorrencias) > 1:
                        raise ErroEntrada(
                            f"Linha {inicio_linha}: coluna {nome_coluna!r} aparece mais de uma vez; "
                            "selecione pelo índice."
                        )
                    indice_coluna = ocorrencias[0]
                elif indice_coluna is not None and indice_coluna >= len(registro):
                    raise ErroEntrada(
                        f"Linha {inicio_linha}: cabeçalho possui {len(registro)} coluna(s); "
                        f"a coluna {indice_coluna + 1} não existe."
                    )
                continue
            primeira_linha = False
            if indice_coluna is not None:
                if indice_coluna >= len(registro):
                    raise ErroEntrada(
                        f"Linha {inicio_linha}: possui {len(registro)} coluna(s); "
                        f"a coluna {indice_coluna + 1} não existe."
                    )
                celulas = [(indice_coluna, registro[indice_coluna])]
            else:
                celulas = list(enumerate(registro))
            for indice, valor in celulas:
                dados.append(
                    _converter_numero(
                        valor,
                        f"Linha {inicio_linha}, coluna {indice + 1}",
                        decimal_virgula=delimitador in (";", "\t"),
                    )
                )
    except csv.Error as exc:
        raise ErroEntrada(f"CSV inválido próximo à linha {leitor.line_num}: {exc}.") from exc
    if not dados:
        raise ErroEntrada(f"O arquivo {arquivo} não contém dados numéricos para analisar.")
    return dados


# ============================================================================
# INTERFACE DE LINHA DE COMANDO
# ============================================================================

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
    """Calcula e apresenta as três partes usando funções independentes."""
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


if __name__ == "__main__":
    raise SystemExit(main())
