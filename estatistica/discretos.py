"""Parte 2: distribuição discreta e medidas obtidas apenas pela tabela."""

from dataclasses import dataclass
import math

from .validacao import validar_dados, validar_tabela_discreta


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
