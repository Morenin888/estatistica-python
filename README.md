# Analisador estatístico em Python

Trabalho de **Probabilidade e Estatística**. O programa analisa números digitados ou dados de um CSV nas três etapas do enunciado.

Repositório: [Morenin888/estatistica-python](https://github.com/Morenin888/estatistica-python), privado. O professor precisa ter acesso ou o proprietário deve alterar a visibilidade conforme a orientação da disciplina.

## Integrantes

Em ordem alfabética:

1. Gabriel Chagas
2. João Vitor Bertolino
3. Marcelo Moreno
4. Marlon

## Arquivos

```text
README.md
main.py
relatorio_tecnico.pdf
```

O código está em `main.py`, com funções pequenas para entrada, cálculo e apresentação. A tabela discreta usa tuplas `(xi, fi, Fi)`; as classes usam dicionários com limites e frequências. O [relatório técnico](relatorio_tecnico.pdf) explica a arquitetura e as fórmulas.

## Execução

Use **Python 3.10 ou superior**. Não é necessário instalar pacotes. Na pasta do projeto, abra o menu:

```bash
python main.py
```

Escolha `1` para digitar números, `2` para carregar CSV ou `0` para sair. Também é possível executar diretamente:

```bash
python main.py -d "1,2,2,3,4"
python main.py --data "1.5,2.5,3.5"
python main.py --dados "1,5;2,5;3,5"
python main.py --data=-2,-1,0,1,2
python main.py --help
```

`-d`, `--data` e `--dados` são nomes da mesma opção. Use vírgula entre números com ponto decimal; para decimal com vírgula, separe os números com ponto e vírgula. Para listas que começam com número negativo, use `--data=...`. Se necessário, substitua `python` por `python3`.

### Arquivos CSV

Crie seu arquivo `dados.csv`. Um exemplo sem cabeçalho é:

```csv
1,2,2,3,4
```

Leia com:

```bash
python main.py -f dados.csv
```

`-f`, `--file` e `--csv` são nomes da mesma opção. Para um CSV com cabeçalho, como:

```csv
id,valor
1,1.5
2,2.5
3,3.5
```

Selecione a coluna pelo nome ou pelo índice, começando em **1**:

```bash
python main.py --file dados.csv --cabecalho --coluna valor
python main.py --csv dados.csv --cabecalho --coluna 2
```

`--cabecalho` declara explicitamente que a primeira linha não vazia contém os nomes das colunas. Sem `--coluna`, todas as células de dados são lidas como números. A leitura aceita UTF-8 e detecta vírgula, ponto e vírgula ou tabulação; decimal com vírgula exige ponto e vírgula ou tabulação como delimitador.

Entrada direta e arquivo são alternativas. `--cabecalho` e `--coluna` acompanham somente um arquivo. Arquivos inválidos, campos vazios, texto, `NaN` e infinito geram mensagens de erro; no menu é possível tentar novamente.

## Bibliotecas por etapa

| Etapa | Implementação |
| --- | --- |
| Parte 1 | Exclusivamente `statistics` para média, mediana e moda, com chamadas diretas a `mean`, `median` e `mode`. |
| Parte 2 | Algoritmos próprios, calculados estritamente pela tabela de frequências. |
| Parte 3 | Fórmulas manuais em Python nativo, sem bibliotecas estatísticas ou de análise de dados como `statistics`, Pandas, NumPy e SciPy. |

`statistics` é importado apenas na função da Parte 1. `math` fornece `log10`/`ceil` para Sturges e verificações numéricas. `csv`, `io` e `pathlib` fazem a leitura; `argparse` e `sys` atendem à interface. As medidas das Partes 2 e 3 são calculadas pelas próprias funções do programa.

## Fórmulas e resultados

Cada entrada válida apresenta as três partes. `n` é o total de observações, `fi` a frequência absoluta e `Fi` a acumulada.

**Parte 1:** média, mediana e moda dos dados brutos. Em empate, `statistics.mode` retorna o primeiro dos valores mais frequentes encontrado na entrada.

**Parte 2:** tabela de valores únicos `xi` ordenados, com `fi` e `Fi`. A média é `Σ(xi·fi)/n`; as modas são os valores de frequência máxima. A mediana localiza, por `Fi`, as posições `piso((n+1)/2)` e `piso((n+2)/2)` e calcula a média entre elas. Se todos os valores ocorrerem uma vez, não há predominância modal.

**Parte 3:** tabela de intervalos, frequências absolutas e acumuladas. O agrupamento e as medidas usam:

```text
k = teto(1 + 3,322 · log10(n))             [Sturges]
h = (máximo − mínimo) / k
mi = (limite inferior + limite superior) / 2
Média = Σ(mi · fi) / n
S(p) = L + ((p · n − F_anterior) / f_classe) · h
Moda de Czuber = L_modal + (d1 / (d1 + d2)) · h
```

Para `S(p)`, escolhe-se a primeira classe de frequência positiva cuja acumulada alcança `p·n`; `L` é seu limite inferior. Na moda, `d1 = f_modal − f_anterior` e `d2 = f_modal − f_seguinte`; vizinhos externos têm frequência zero.

| Medida | Proporção p |
| --- | ---: |
| Mediana | 0,50 |
| Q1 e Q3 | 0,25 e 0,75 |
| D2 e D7 | 0,20 e 0,70 |
| P15 e P22 | 0,15 e 0,22 |
| P63 e P70 | 0,63 e 0,70 |

As classes são `[Li, Ls)`, com a última fechada para incluir o máximo; classes vazias são preservadas. Dados constantes geram uma classe `[v, v]` e todas as medidas iguais a `v`. Nas demais distribuições, empates entre classes modais são informados; frequências uniformes, frequência máxima `1` ou denominador `d1+d2 = 0` impedem afirmar uma moda única.

As medidas intervalares são estimativas por pontos médios e interpolação. Para conferir uma entrada simples, `1,2,2,3,4` produz média **2,4**, mediana **2** e moda **2** nas Partes 1 e 2. `D7` e `P70` representam a mesma posição na Parte 3.

Validação local: 61 testes de cálculos, entradas e execução da CLI passaram, incluindo dados constantes, CSV com cabeçalho e as restrições de bibliotecas por etapa.

Referências: [documentação de statistics](https://docs.python.org/3/library/statistics.html) e [material da UFSC sobre as modas de King e Czuber](https://www.inf.ufsc.br/~marcelo/Moda.PDF).
