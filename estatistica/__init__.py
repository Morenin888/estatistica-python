"""API pública do analisador estatístico descritivo."""

from .validacao import validar_dados, validar_tabela_discreta
from .nao_agrupados import ResultadoNaoAgrupados, analisar_nao_agrupados
from .discretos import (LinhaDiscreta, ResultadoDiscretos,
                        construir_tabela_discreta, calcular_medidas_discretas)
from .classes import (Classe, DistribuicaoClasses, ResultadoClasses,
                      construir_distribuicao, criar_distribuicao_manual,
                      calcular_medidas_classes, calcular_separatriz)

__all__ = [
    "validar_dados", "validar_tabela_discreta", "ResultadoNaoAgrupados",
    "analisar_nao_agrupados", "LinhaDiscreta", "ResultadoDiscretos",
    "construir_tabela_discreta", "calcular_medidas_discretas", "Classe",
    "DistribuicaoClasses", "ResultadoClasses", "construir_distribuicao",
    "criar_distribuicao_manual", "calcular_medidas_classes", "calcular_separatriz",
]
