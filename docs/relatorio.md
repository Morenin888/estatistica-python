# Analisador estatístico em Python

Relatório técnico — Probabilidade e Estatística

**Integrantes, em ordem alfabética:** Gabriel Chagas; João Vitor Bertolino; Marcelo Moreno; Marlon.

**Data:** 6 de outubro de 2026. **Entrega prevista no enunciado:** 10 de outubro de 2026.

## 1. Objetivo e organização

O projeto implementa uma aplicação de linha de comando (CLI) para analisar dados numéricos digitados no terminal ou lidos de um arquivo CSV. O mesmo conjunto de observações é processado em três representações: dados não agrupados, tabela de frequências discretas e distribuição com intervalos de classe. São apresentados moda, média e mediana nas três partes, além das separatrizes exigidas para a distribuição intervalar.

A aplicação utiliza Python 3.10 ou superior e apenas a biblioteca padrão durante sua execução. O pacote statistics fica restrito ao módulo da Parte 1. As Partes 2 e 3 executam diretamente os algoritmos e as fórmulas, sem Pandas, NumPy, SciPy ou chamadas a statistics.

| Arquivo ou diretório | Responsabilidade |
| --- | --- |
| main.py; estatistica/__main__.py | Pontos de entrada para execução |
| estatistica/cli.py | Menu, argumentos e apresentação das tabelas |
| estatistica/entrada.py | Conversão dos dados e leitura de CSV |
| estatistica/validacao.py | Validação de dados e tabelas |
| estatistica/nao_agrupados.py | Parte 1: funções nativas de statistics |
| estatistica/discretos.py | Parte 2: frequências por valor e medidas exatas |
| estatistica/classes.py | Parte 3: Sturges, classes e interpolação |
| tests/; dados/; docs/ | Testes, exemplos e documentação |

O fluxo principal é: entrada → validação → cálculo das três partes → exibição. A separação entre entrada, cálculo e apresentação permite testar as fórmulas independentemente da interface.

## 2. Entrada e tratamento de erros

A entrada manual aceita números separados por vírgula com ponto decimal, como 1.5,2.5,3. Quando o separador é ponto e vírgula, também é possível usar a vírgula decimal: 1,5;2,5;3. Arquivos CSV podem usar vírgula, ponto e vírgula ou tabulação. O cabeçalho deve ser indicado explicitamente por --cabecalho; --coluna permite selecionar uma coluna pelo nome ou pelo índice, contado a partir de 1.

São rejeitados conjuntos vazios, campos vazios em registros preenchidos, texto em campos numéricos, NaN e infinitos. Os erros de CSV identificam a linha e a coluna quando aplicável. Arquivos inexistentes, ilegíveis ou com estrutura inválida geram mensagens claras. No menu, a entrada inválida permite nova tentativa; EOF e Ctrl+C encerram a execução de forma controlada.

<!-- pagina -->

## 3. Implementação das medidas estatísticas

### 3.1. Parte 1 — Dados não agrupados

As três medidas são obtidas diretamente por statistics.mean(dados), statistics.median(dados) e statistics.mode(dados), conforme a restrição do enunciado. Em caso de empate na maior frequência, mode retorna o primeiro valor encontrado entre os empatados [1]. A interface explica essa convenção para que ela seja distinguida do resultado multimodal da Parte 2.

### 3.2. Parte 2 — Tabela discreta

Um dicionário conta as ocorrências de cada valor. As chaves são ordenadas e dão origem às linhas (xi, fi, Fi), nas quais xi é o valor observado, fi sua frequência absoluta e Fi a soma das frequências até a linha atual. As medidas usam exclusivamente essa tabela, sem reconstruir os dados brutos.

**Média:** μ = Σ(xi · fi) / n, com n = Σfi. No código, o somatório usa uma escala comum e pesos fi/n, uma forma algebricamente equivalente que evita produtos intermediários excessivamente grandes.

**Mediana:** para n ímpar, localiza-se a posição (n + 1)/2 pela primeira frequência acumulada que a alcança. Para n par, localizam-se as posições n/2 e n/2 + 1 e calcula-se a média dos dois valores correspondentes.

**Moda:** identifica-se a maior fi e retornam-se todos os valores que a possuem. Quando todos os valores aparecem apenas uma vez, a aplicação informa que não há moda predominante, embora todos estejam empatados em frequência.

### 3.3. Parte 3 — Construção das classes

**Sturges:** k = ceil(1 + 3,322 · log10(n)). O arredondamento para cima é uma decisão explícita da implementação. A amplitude total é A = máximo − mínimo; a amplitude da classe é h = A/k.

Os limites são construídos a partir do mínimo com largura h. Os intervalos são fechados à esquerda e abertos à direita: [Li, Ls). O último intervalo inclui o máximo: [Li, Ls]. Cada observação pertence a exatamente uma classe; fi é contado e Fi é acumulado. Classes vazias são preservadas. Não há arredondamento dos limites antes dos cálculos.

**Média estimada:** μ = Σ(mi · fi)/n, com mi = (Li + Ls)/2, o ponto médio de cada classe.

**Interpolação:** S(p) = L + [(p · n − Fantes)/f] · h. A busca identifica a primeira classe não vazia cuja frequência acumulada alcança p · n. L é seu limite inferior, Fantes é a frequência acumulada anterior e f é a frequência absoluta da classe. A mediana usa p = 0,50; quartis usam 0,25 e 0,75; decis usam 0,20 e 0,70; percentis usam 0,15; 0,22; 0,63 e 0,70.

**Moda de Czuber [2]:** Mo = L + [Δ1/(Δ1 + Δ2)] · h, com Δ1 = fm − fant e Δ2 = fm − fpost. A classe modal possui a maior frequência; nas extremidades, a frequência da classe vizinha inexistente é convencionada como zero. Empates entre classes modais são informados. Se Δ1 + Δ2 = 0, não se força uma estimativa única.

Quando todos os dados são iguais, A = 0. Nesse caso, constrói-se uma única classe degenerada [v, v] e todas as medidas retornam v, evitando divisão por zero. Fora desse caso, resultados intervalares são estimativas: o agrupamento perde a posição exata dos dados dentro de cada classe.

<!-- pagina -->

## 4. Exemplo reproduzível e conferência manual

O arquivo dados/exemplo.csv contém 48 observações inteiras. A distribuição discreta usa os valores 0 a 7 com frequências 2, 4, 8, 12, 10, 6, 4 e 2. Portanto, Σxi·fi = 164; média = 164/48 = 3,416667. As posições 24 e 25 pertencem ao valor 3, logo a mediana é 3; a moda também é 3, com frequência 12.

Sturges produz k = ceil(1 + 3,322 · log10(48)) = 7. Como A = 7 − 0 = 7, tem-se h = 1. O máximo 7 pertence à última classe, que também contém o valor 6.

| Intervalo | Ponto médio mi | fi | Fi |
| --- | --- | --- | --- |
| [0, 1) | 0,5 | 2 | 2 |
| [1, 2) | 1,5 | 4 | 6 |
| [2, 3) | 2,5 | 8 | 14 |
| [3, 4) | 3,5 | 12 | 26 |
| [4, 5) | 4,5 | 10 | 36 |
| [5, 6) | 5,5 | 6 | 42 |
| [6, 7] | 6,5 | 6 | 48 |

**Média intervalar:** Σmi·fi = 186, portanto μ = 186/48 = 3,875000.

**Mediana intervalar:** a posição n/2 = 24 está na classe [3, 4). Assim, Md = 3 + [(24 − 14)/12] · 1 = 3,833333.

**Moda de Czuber:** a classe modal é [3, 4); Δ1 = 12 − 8 = 4 e Δ2 = 12 − 10 = 2. Logo, Mo = 3 + [4/(4 + 2)] · 1 = 3,666667.

| Separatriz | p | Posição p · n | Valor estimado |
| --- | --- | --- | --- |
| Q1 | 0,25 | 12,00 | 2,750000 |
| Q3 | 0,75 | 36,00 | 5,000000 |
| D2 | 0,20 | 9,60 | 2,450000 |
| D7 | 0,70 | 33,60 | 4,760000 |
| P15 | 0,15 | 7,20 | 2,150000 |
| P22 | 0,22 | 10,56 | 2,570000 |
| P63 | 0,63 | 30,24 | 4,424000 |
| P70 | 0,70 | 33,60 | 4,760000 |

Por exemplo, P63 está na classe [4, 5), cuja frequência anterior é 26 e cuja frequência absoluta é 10: P63 = 4 + [(30,24 − 26)/10] · 1 = 4,424. D7 e P70 coincidem porque representam a mesma proporção acumulada. As diferenças entre as Partes 1/2 e a Parte 3 são esperadas, pois a terceira parte usa pontos médios e interpolação.

<!-- pagina -->

## 5. Execução e validação

Não é necessário instalar pacotes para executar o analisador. Após obter o projeto, abra o terminal na pasta estatistica-python e use Python 3.10 ou superior. Em sistemas nos quais o comando se chama python3, substitua python por python3.

```text
python main.py
python -m estatistica --dados "1,2,2,3,4"
python main.py --csv dados/exemplo.csv
python main.py --csv dados/com_cabecalho.csv --cabecalho --coluna valor
python main.py --csv dados/decimais.csv --cabecalho --coluna medida
python -m unittest discover -s tests -v
```

A primeira forma abre o menu interativo. As demais processam os dados diretamente ou executam os testes. A ajuda completa pode ser consultada com python main.py --help. A saída mostra o tamanho da amostra, as três partes, suas tabelas e todas as separatrizes solicitadas.

A verificação automatizada utiliza unittest, da biblioteca padrão. A suíte confere casos com quantidade par e ímpar de observações, valores negativos e decimais, amostras unitárias, dados constantes, modas empatadas, limites entre classes, inclusão do máximo, classes vazias e tabelas de referência calculadas manualmente. Também verifica entradas manuais e CSV, erros de conversão, cabeçalhos, seleção de coluna e a execução da CLI.

Os oráculos matemáticos incluem a tabela de classes [18, 22), [22, 26), [26, 30), [30, 34], com frequências 32, 45, 28 e 15. Seus resultados corretos são média 24,866667; mediana 24,488889; moda de Czuber 23,733333. Esses valores são calculados pelas fórmulas, pois os números ilustrativos de saída no enunciado não correspondem à tabela apresentada.

**Resultado da verificação:** 60 testes aprovados, sem falhas, em 6 de outubro de 2026. **Ambiente utilizado:** Python 3.12.14. A configuração em .github/workflows/testes.yml prevê executar a suíte no GitHub em outras versões; essa configuração não substitui um resultado observado do serviço.

## 6. Entrega e limites

O projeto é entregue no repositório privado https://github.com/Morenin888/estatistica-python, com código modular, arquivos CSV, testes, README.md e este relatório em PDF e Markdown. docs/CHECKLIST.md relaciona os requisitos; docs/GITHUB.md orienta execução, atualização e concessão de acesso ao professor antes da entrega.

O programa trabalha com números reais finitos em ponto flutuante. Valores fora da capacidade de representação numérica recebem mensagem de erro. A frequência discreta mantém os valores observados, enquanto as classes fornecem aproximações. A convenção de Sturges, a inclusão do máximo e as regras de empate são documentadas para tornar os resultados reproduzíveis.

## Referências

[1] Python Software Foundation. statistics — Funções estatísticas, documentação do Python 3.10. Disponível em: https://docs.python.org/pt-br/3.10/library/statistics.html. Acesso em: 6 out. 2026.

[2] Universidade Federal de Santa Catarina, material didático disponibilizado no Departamento de Informática e Estatística. Moda de King e Moda de Czuber. Disponível em: https://www.inf.ufsc.br/~marcelo/Moda.PDF. Acesso em: 6 out. 2026. Utilizado para a fórmula da moda intervalar e sua interpretação como estimativa.

[3] Trabalho de Estatística em Python. Enunciado fornecido para a disciplina Probabilidade e Estatística, com prazo de entrega em 10 out. 2026. Utilizado para requisitos, separatrizes e formato de entrega.
