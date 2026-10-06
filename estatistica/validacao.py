"""Validação comum de dados e tabelas, independente das fórmulas estatísticas."""

import math


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
