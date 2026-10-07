# Analisador estatístico em Python

Trabalho de **Probabilidade e Estatística**: aplicação de linha de comando para analisar números digitados ou dados de um arquivo CSV nas três partes exigidas pelo enunciado.

Repositório: [Morenin888/estatistica-python](https://github.com/Morenin888/estatistica-python), privado. Para acessá-lo, é necessário usar uma conta autorizada. O professor precisa receber acesso ou o proprietário deve tornar o repositório público, conforme a orientação da disciplina.

## Integrantes em ordem alfabética

1. Gabriel Chagas
2. João Vitor Bertolino
3. Marcelo Moreno
4. Marlon

## Arquivos da entrega

```text
README.md
main.py
relatorio_tecnico.pdf
```

Todo o programa está em `main.py`, organizado internamente em funções de leitura, validação, cálculo de cada parte e apresentação. Os cálculos permanecem separados da interface. O [relatório técnico em PDF](relatorio_tecnico.pdf) explica a arquitetura, as fórmulas e a execução.

## Executar

É necessário **Python 3.10 ou superior**. O programa usa somente a biblioteca padrão, sem instalação de pacotes externos. Abra o terminal na pasta do projeto:

```bash
python main.py
```

O menu permite digitar números, carregar CSV ou sair pela opção `0`. Também é possível informar a entrada diretamente:

```bash
python main.py --dados "1,2,2,3,4"
python main.py --dados "1.5,2.5,3.5"
python main.py --dados "1,5;2,5;3,5"
python main.py --dados=-2,-1,0,1,2
python main.py --help
```

Use vírgula para separar números com **ponto decimal**. Para usar **vírgula decimal**, separe os números com ponto e vírgula. Se a lista começar com um número negativo, use `--dados=...`. Em sistemas que usam o comando `python3`, substitua `python` por `python3`.

### Ler um CSV

Crie um arquivo de entrada chamado `dados.csv`, por exemplo, com esta linha numérica, sem cabeçalho:

```csv
1,2,2,3,4
```

Execute:

```bash
python main.py --csv dados.csv
```

Para um arquivo com cabeçalho e mais de uma coluna, por exemplo:

```csv
id,valor
1,1.5
2,2.5
3,3.5
```

Selecione a coluna desejada:

```bash
python main.py --csv dados.csv --cabecalho --coluna valor
python main.py --csv dados.csv --cabecalho --coluna 2
```

O arquivo deve ser UTF-8. O programa detecta vírgula, ponto e vírgula ou tabulação como delimitadores. Decimal com vírgula é aceito quando o delimitador é ponto e vírgula ou tabulação. `--cabecalho` declara explicitamente a primeira linha não vazia como cabeçalho; `--coluna` aceita índice começando em **1** ou nome exato, que exige cabeçalho. Sem seleção de coluna, todas as células de dados devem ser numéricas.

`--dados` e `--csv` são alternativas; `--coluna` e `--cabecalho` só acompanham `--csv`. Arquivos inexistentes, dados vazios, células vazias, texto, `NaN` e infinito geram mensagens de erro. No menu é possível tentar novamente. Pela linha de comando, a saída é `0` para sucesso, `1` para erro nos dados e `2` para argumentos inválidos.

## Cálculos e saída

Cada entrada válida apresenta as três partes. Nas fórmulas, `n` é o total de observações, `fi` a frequência absoluta e `Fi` a frequência acumulada.

**Parte 1 — dados não agrupados:** média, mediana e moda calculadas diretamente por `statistics.mean`, `statistics.median` e `statistics.mode`, conforme a restrição do trabalho. Em empate, `statistics.mode` retorna o primeiro dos valores mais frequentes encontrado na entrada.

**Parte 2 — agrupamento sem intervalos:** tabela de valores únicos `xi` em ordem crescente, com `fi` e `Fi`. Os cálculos usam apenas a tabela:

```text
n = Σ fi
Fi = soma das frequências até a linha i
Média = Σ(xi · fi) / n
Moda(s) = valores com frequência máxima
Mediana = média dos valores nas posições centrais, localizados por Fi
```

As posições centrais são `piso((n + 1)/2)` e `piso((n + 2)/2)`. Todas as modas empatadas são apresentadas; se cada valor ocorrer uma vez, o programa informa a ausência de predominância modal.

**Parte 3 — agrupamento com intervalos:** fórmulas em Python nativo, sem `statistics` ou bibliotecas como Pandas, NumPy e SciPy. A tabela mostra intervalo, `fi`, `Fi` e ponto médio:

```text
k = teto(1 + 3,322 · log10(n))             [Sturges]
A = máximo − mínimo
h = A / k
mi = (limite inferior + limite superior) / 2
Média agrupada = Σ(mi · fi) / n
S(p) = L + ((p · n − F_anterior) / f_classe) · h
Moda de Czuber = L_modal + (d1 / (d1 + d2)) · h
```

Na interpolação `S(p)`, a classe é a primeira com frequência positiva cuja acumulada alcança `p·n`; `L` é seu limite inferior. Na moda, `d1 = f_modal − f_anterior` e `d2 = f_modal − f_seguinte`; vizinhos externos têm frequência zero.

| Medida de posição | Proporção usada em S(p) |
| --- | ---: |
| Mediana | 0,50 |
| Q1 e Q3 | 0,25 e 0,75 |
| D2 e D7 | 0,20 e 0,70 |
| P15 e P22 | 0,15 e 0,22 |
| P63 e P70 | 0,63 e 0,70 |

As classes são `[Li, Ls)`, com a última fechada para incluir o máximo. Classes vazias são preservadas. Dados constantes geram uma única classe `[v, v]`, com todas as medidas iguais a `v`. Nas demais distribuições, empates entre classes modais são informados; não se afirma uma moda única quando todas as classes têm a mesma frequência ou quando a frequência máxima é `1`. Trechos com `d1 + d2 = 0` não permitem interpolação da moda.

As medidas agrupadas são estimativas por pontos médios e interpolação, podendo diferir das medidas exatas das Partes 1 e 2. Para conferir uma entrada simples, `1,2,2,3,4` deve produzir média **2,4**, mediana **2** e moda **2** nas Partes 1 e 2. `D7` e `P70` sempre representam a mesma posição na Parte 3.

Referências: [documentação oficial de statistics](https://docs.python.org/3/library/statistics.html) e [material sobre as modas de King e Czuber disponibilizado pela UFSC](https://www.inf.ufsc.br/~marcelo/Moda.PDF).
