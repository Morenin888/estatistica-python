# Conferência do enunciado

Este documento relaciona os requisitos à implementação e aos materiais da entrega. O enunciado atribui 1,0 ponto a cada uma das três partes; a avaliação considera corretude dos algoritmos, qualidade do código e relatório técnico.

| Requisito | Evidência no projeto |
| --- | --- |
| CLI com digitação manual ou leitura de CSV | `main.py`, `estatistica/__main__.py`, `estatistica/cli.py` e `estatistica/entrada.py`; menu e opções `--dados`/`--csv` |
| Equipe de no máximo cinco integrantes | Quatro integrantes no README e no relatório, em ordem alfabética: Gabriel Chagas; João Vitor Bertolino; Marcelo Moreno; Marlon |
| Parte 1: média, mediana e moda com funções diretas de `statistics` | `estatistica/nao_agrupados.py`: `statistics.mean`, `statistics.median` e `statistics.mode` |
| Parte 2: distribuição discreta em tabela | `estatistica/discretos.py`; a CLI apresenta valores ordenados, frequências absolutas e acumuladas |
| Parte 2: média, mediana e moda calculadas pela tabela | Somatório ponderado, posições centrais por acumuladas e seleção das frequências máximas em `estatistica/discretos.py` |
| Parte 3: Python nativo, sem biblioteca estatística ou de análise de dados | `estatistica/classes.py`; não usa `statistics`, Pandas, NumPy ou SciPy |
| Parte 3: quantidade de classes por Sturges e amplitude | `k = teto(1 + 3,322 log10(n))` e `h = (máximo − mínimo)/k` |
| Parte 3: tabela de intervalo, frequência absoluta e acumulada | Classes `[Li, Ls)`, com última classe fechada no máximo; colunas intervalo, `fi`, `Fi` e ponto médio na CLI |
| Parte 3: média agrupada | Somatório de pontos médios ponderados pelas frequências |
| Parte 3: mediana interpolada | `S(0,50)`, com `S(p) = L + ((p·n − F_anterior)/f_classe)·h` |
| Parte 3: moda por King ou Czuber | Método de Czuber; diferenças de frequência entre a classe modal e suas vizinhas |
| Parte 3: Q1 e Q3 | `S(0,25)` e `S(0,75)` |
| Parte 3: D2 e D7 | `S(0,20)` e `S(0,70)` |
| Parte 3: P15, P22, P63 e P70 | `S(0,15)`, `S(0,22)`, `S(0,63)` e `S(0,70)` |
| Modularização e funções bem definidas | Leitura, validação, três módulos de cálculo e apresentação separados no pacote `estatistica` |
| Exceções: arquivo inválido, texto em vez de número e dados vazios | Erros explicativos na entrada manual/CSV; rejeição de células vazias e números não finitos; testes de entrada |
| Clareza na apresentação | Cabeçalhos de três partes, tabelas alinhadas, medidas nomeadas e avisos sobre empates/estimativas |
| Corretude e casos de fronteira | `tests/test_calculos.py` e `tests/test_entrada_cli.py`; execute `python -m unittest discover -s tests -v` |
| Relatório breve com arquitetura, tradução das fórmulas e execução | `docs/relatorio.pdf`, com fonte `docs/relatorio.md`; instruções também no README |
| Entrega: código-fonte no GitHub e relatório em PDF | Repositório criado em [Morenin888/estatistica-python](https://github.com/Morenin888/estatistica-python); código e PDF preparados no projeto; publicação e acesso devem ser conferidos conforme `docs/GITHUB.md` |

## Convenções matemáticas explícitas

- Valores no limite entre classes entram na classe à direita; o máximo entra na última classe.
- Dados constantes geram uma classe efetiva de amplitude zero e todas as medidas iguais ao valor observado.
- A Parte 1 segue o comportamento de `statistics.mode` nos empates. A Parte 2 apresenta todos os valores de frequência máxima. A Parte 3 explicita classes modais empatadas e casos sem interpolação única.
- Classes vazias não são escolhidas para interpolar separatrizes.
- Medidas agrupadas são estimativas; a média e a mediana das Partes 1 e 2 permanecem exatas para os valores recebidos, respeitada a representação numérica usada pelo Python.
- Os números ilustrativos do enunciado não são uma referência de teste: por exemplo, os intervalos `[18,22)`, `[22,26)`, `[26,30)` e `[30,34]` com frequências `32,45,28,15` resultam em média agrupada `24,866667`, mediana `24,488889` e moda de Czuber `23,733333`. A validação usa as fórmulas e tabelas, pois a ilustração contém resultados incompatíveis com suas próprias frequências.

## Passos finais de submissão

- [x] Repositório criado na conta escolhida: [Morenin888/estatistica-python](https://github.com/Morenin888/estatistica-python), privado.
- [ ] Confirmar que o código-fonte, exemplos, testes e relatório PDF estão publicados no repositório.
- [ ] Confirmar a aprovação do workflow de testes na aba Actions para o commit publicado.
- [ ] Garantir que o professor pode acessar o repositório.
- [ ] Entregar a URL real do repositório e `docs/relatorio.pdf` até **10 de outubro de 2026**, conforme o enunciado.

Estes passos externos não são marcados como concluídos apenas pela existência dos arquivos locais.
