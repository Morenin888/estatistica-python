"""Parte 3: classes de Sturges e fórmulas clássicas de interpolação.

Este módulo não utiliza statistics nem bibliotecas de análise de dados.
"""

from dataclasses import dataclass
import math

from .validacao import validar_dados, validar_frequencia, validar_numero


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
