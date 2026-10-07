# Analisador estatístico em Python

Trabalho de **Probabilidade e Estatística**, com entrega de código-fonte no GitHub e relatório em PDF. A aplicação de linha de comando lê números digitados ou um arquivo CSV e apresenta as três análises exigidas pelo enunciado.

Repositório do grupo: [Morenin888/estatistica-python](https://github.com/Morenin888/estatistica-python).

## Integrantes em ordem alfabética

1. Gabriel Chagas
2. João Vitor Bertolino
3. Marcelo Moreno
4. Marlon

## Execução

É necessário **Python 3.10 ou superior**. A aplicação e os testes usam somente a biblioteca padrão; não é necessário instalar pacotes com `pip`.

Abra o terminal na pasta do projeto. Para usar o menu interativo:

```bash
python main.py
```

Também é possível executar como módulo, inclusive com as mesmas opções:

```bash
python -m estatistica
python -m estatistica --dados "1,2,2,3,4,4,4,5"
```

Em sistemas nos quais o executável é `python3`, substitua `python` por `python3` nos comandos.

### Entrada direta e arquivos CSV

```bash
python main.py --dados "1,2,2,3,4,4,4,5"
python main.py --dados "1,5;2,5;3,5"
python main.py --dados=-2,-1,0,1,2
python main.py --csv dados/exemplo.csv
python main.py --csv dados/com_cabecalho.csv --cabecalho --coluna valor
python main.py --csv dados/com_cabecalho.csv --cabecalho --coluna 2
python main.py --csv dados/decimais.csv --cabecalho --coluna medida
python main.py --help
```

- `--dados`: use vírgula entre valores com ponto decimal, como `1.5,2.5,3.5`. Para decimal com vírgula, separe os valores com ponto e vírgula, como `1,5;2,5;3,5`. Use `--dados=...` quando a lista começar com um número negativo.
- `--csv`: lê um arquivo UTF-8, com ou sem BOM; detecta delimitadores vírgula, ponto e vírgula ou tabulação. Decimal com vírgula é aceito com ponto e vírgula ou tabulação.
- `--cabecalho`: informa explicitamente que a primeira linha não vazia contém nomes de colunas; o programa não adivinha a existência de cabeçalho.
- `--coluna`: seleciona uma coluna pelo índice, começando em **1**, ou pelo nome exato do cabeçalho. Seleção por nome exige `--cabecalho`.

Sem `--coluna`, todas as células de dados são lidas como números; selecione uma coluna quando o CSV também possuir identificadores ou texto. Linhas vazias são ignoradas, mas células vazias, texto, `NaN` e infinito são rejeitados. `--dados` e `--csv` são mutuamente exclusivos; `--coluna` e `--cabecalho` só podem acompanhar `--csv`.

Cada entrada válida executa as três partes. No menu, erros são apresentados e permitem nova tentativa; a opção `0` encerra. Na execução por argumentos, o código de saída é `0` para sucesso, `1` para erro nos dados e `2` para argumentos inválidos.

## Organização

```text
estatistica-python/
├── .github/workflows/testes.yml
├── .gitignore
├── README.md
├── main.py
├── estatistica/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── entrada.py
│   ├── validacao.py
│   ├── nao_agrupados.py
│   ├── discretos.py
│   └── classes.py
├── dados/
│   ├── exemplo.csv
│   ├── com_cabecalho.csv
│   └── decimais.csv
├── docs/
│   ├── relatorio.pdf
│   ├── relatorio.md
│   ├── GITHUB.md
│   └── CHECKLIST.md
└── tests/
    ├── test_calculos.py
    └── test_entrada_cli.py
```

`entrada.py` interpreta os dados; `validacao.py` verifica os números e as tabelas. Os três módulos de cálculo atendem separadamente às partes do trabalho. `cli.py` apresenta os resultados e trata erros; `main.py` e `__main__.py` são pontos de entrada. Os cálculos não dependem da interface.

## Métodos e fórmulas

Nas fórmulas, `n` é o total de observações, `fi` a frequência absoluta e `Fi` a frequência acumulada. Em qualquer tabela, `n = Σ fi` e `Fi = Σ(j ≤ i) fj`.

### Parte 1 — dados não agrupados

O módulo `nao_agrupados.py` chama diretamente `statistics.mean`, `statistics.median` e `statistics.mode`, conforme a regra do enunciado. Em empate, `statistics.mode` devolve o primeiro dos valores mais frequentes encontrado na entrada; a interface explica essa convenção.

### Parte 2 — dados agrupados sem intervalos

A tabela contém os valores únicos `xi`, em ordem crescente, acompanhados de `fi` e `Fi`. As medidas são calculadas **a partir dessa tabela**, sem chamadas a bibliotecas estatísticas:

```text
Média = Σ(xi · fi) / n
Moda(s) = valores xi cuja frequência fi é máxima
r1 = piso((n + 1) / 2)
r2 = piso((n + 2) / 2)
Mediana = (valor_na_posição(r1) + valor_na_posição(r2)) / 2
```

`valor_na_posição(r)` é o primeiro `xi` cujo `Fi ≥ r`; assim, a mediana funciona para `n` par e ímpar sem reconstruir a lista original. Todas as modas empatadas são apresentadas. Quando cada valor ocorre apenas uma vez, o programa informa que não há predominância modal.

### Parte 3 — dados agrupados com intervalos

O módulo `classes.py` usa Python nativo e funções matemáticas da biblioteca padrão, sem `statistics`, Pandas, NumPy ou SciPy.

```text
k = teto(1 + 3,322 · log10(n))                    [Sturges]
A = máximo − mínimo
h = A / k
Li = mínimo + i · h, para i = 0, ..., k − 1
Ls = mínimo + (i + 1) · h
mi = (Li + Ls) / 2                              [ponto médio]
Média agrupada = Σ(mi · fi) / n
```

As classes são fechadas à esquerda e abertas à direita, `[Li, Ls)`, exceto a última, `[Li, máximo]`, que inclui o maior valor. A tabela explicita intervalo, `fi`, `Fi` e ponto médio. Classes vazias são preservadas. Se todos os dados forem iguais a `v`, há uma única classe efetiva `[v, v]`, de amplitude zero, e todas as medidas são `v`; o número teórico de classes de Sturges fica disponível separadamente.

A mediana e as demais separatrizes usam a mesma interpolação. Para uma proporção `p`, encontra-se a primeira classe de frequência positiva cuja acumulada alcança `p · n`:

```text
S(p) = L + ((p · n − F_anterior) / f_classe) · h
Mediana = S(0,50)
Q1 = S(0,25)          Q3 = S(0,75)
D2 = S(0,20)          D7 = S(0,70)
P15 = S(0,15)         P22 = S(0,22)
P63 = S(0,63)         P70 = S(0,70)
```

`L` é o limite inferior da classe selecionada, `F_anterior` a frequência acumulada anterior e `f_classe` sua frequência absoluta. Como `D7` e `P70` representam a mesma posição, seus resultados são iguais.

A moda agrupada usa o **método de Czuber**:

```text
d1 = f_modal − f_anterior
d2 = f_modal − f_seguinte
Moda = L_modal + (d1 / (d1 + d2)) · h
```

Para classes modais nas extremidades, a frequência do vizinho externo é zero. Em empate, o resultado identifica as classes modais e apresenta as estimativas possíveis, quando definidas, sem afirmar uma moda única. Quando todas as classes têm a mesma frequência, não se apresenta uma moda interpolada. Quando `d1 + d2 = 0`, a interpolação naquele trecho é indefinida; quando a maior frequência é `1`, não se atribui predominância modal.

As medidas da Parte 3 são **estimativas**: pontos médios representam cada classe e a interpolação supõe distribuição uniforme dentro da classe. Por isso, podem diferir das medidas exatas das Partes 1 e 2.

## Exemplo conferível

`dados/exemplo.csv` contém 48 observações, com frequências de `0` a `7` iguais a `2, 4, 8, 12, 10, 6, 4, 2`. Execute:

```bash
python main.py --csv dados/exemplo.csv
```

| Medida | Partes 1 e 2 | Parte 3 |
| --- | ---: | ---: |
| Média | 3,416667 | 3,875 |
| Mediana | 3 | 3,833333 |
| Moda | 3 | 3,666667 |

Na Parte 3, `k = 7`, `h = 1` e as frequências das classes são `2, 4, 8, 12, 10, 6, 6`. A última classe `[6, 7]` reúne tanto o valor `6` quanto o máximo `7`. As separatrizes são `Q1 = 2,75`, `Q3 = 5`, `D2 = 2,45`, `D7 = 4,76`, `P15 = 2,15`, `P22 = 2,57`, `P63 = 4,424` e `P70 = 4,76`.

## Verificação e entrega

Execute os testes a partir da raiz do projeto:

```bash
python -m unittest discover -s tests -v
```

Os testes conferem resultados matemáticos, casos de empate e dados constantes, limites das classes, separatrizes, entrada manual, CSV, erros e a execução da CLI. O workflow do GitHub Actions está configurado para executar a suíte e um exemplo CSV em Python 3.10, 3.12 e 3.13.

Validação realizada: **60 testes aprovados localmente**, com a mesma suíte e o exemplo CSV aprovados nas três versões de Python no [GitHub Actions](https://github.com/Morenin888/estatistica-python/actions/runs/37558053841).

- [Relatório técnico em PDF](docs/relatorio.pdf) e [fonte editável](docs/relatorio.md).
- [Checklist dos requisitos do enunciado](docs/CHECKLIST.md).
- [Acesso ao repositório, execução e atualizações no GitHub](docs/GITHUB.md).

Referência da Parte 1: [documentação oficial do módulo `statistics`](https://docs.python.org/3/library/statistics.html).

Referência da moda intervalar: [Moda de King e Moda de Czuber, material disponibilizado pela UFSC](https://www.inf.ufsc.br/~marcelo/Moda.PDF).
