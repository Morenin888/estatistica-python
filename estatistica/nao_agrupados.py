"""Parte 1: as três medidas são calculadas diretamente por statistics.

A entrada deve ser validada com validar_dados antes de chamar esta função.
statistics.mode escolhe a primeira moda encontrada quando há empate.
"""

import statistics


class ResultadoNaoAgrupados:
    """Resultado simples para preservar statistics como única importação."""

    def __init__(self, media, mediana, moda):
        self.media = media
        self.mediana = mediana
        self.moda = moda


def analisar_nao_agrupados(dados):
    """Aplica mean, median e mode diretamente aos dados já validados."""
    return ResultadoNaoAgrupados(
        media=statistics.mean(dados),
        mediana=statistics.median(dados),
        moda=statistics.mode(dados),
    )
