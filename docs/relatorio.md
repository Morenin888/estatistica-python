# Relatório técnico

Analisador estatístico em Python — Probabilidade e Estatística

**Integrantes:** Gabriel Chagas; João Vitor Bertolino; Marcelo Moreno; Marlon.

## 1. Objetivo e arquitetura

A aplicação de linha de comando recebe números digitados ou um arquivo CSV e realiza três análises: dados não agrupados, frequências discretas e intervalos de classe. Utiliza Python 3.10 ou superior, somente com a biblioteca padrão.

O projeto separa a interface (cli.py), a leitura (entrada.py), a validação (validacao.py) e os cálculos (nao_agrupados.py, discretos.py e classes.py). main.py inicia o programa. Essa organização permite testar os cálculos independentemente da entrada e da apresentação.

## 2. Cálculos e fórmulas de interpolação

**Parte 1:** média, mediana e moda são calculadas diretamente por statistics.mean, statistics.median e statistics.mode. O módulo statistics é utilizado apenas nesta parte.

**Parte 2:** um dicionário conta as frequências fi de cada valor xi. A tabela é ordenada e acumula Fi. A média usa Σ(xi · fi)/n; a mediana localiza as posições centrais pela frequência acumulada; a moda seleciona os valores de maior frequência.

**Parte 3:** as classes usam Sturges, k = ceil(1 + 3,322 · log10(n)), e amplitude h = (máximo − mínimo)/k. O último intervalo inclui o máximo. A média usa pontos médios ponderados pelas frequências.

**Separatrizes:** S(p) = L + [(p · n − Fantes)/f] · h. No código, uma busca percorre as frequências acumuladas até localizar a classe da posição p · n; depois aplica a fórmula. L é o limite inferior, Fantes a acumulada anterior e f a frequência da classe. A mesma função calcula mediana, Q1, Q3, D2, D7, P15, P22, P63 e P70, alterando p.

**Moda de Czuber:** Mo = L + [Δ1/(Δ1 + Δ2)] · h, com Δ1 e Δ2 iguais às diferenças entre a frequência modal e as frequências das classes anterior e seguinte. As medidas intervalares são estimativas. Dados constantes retornam o próprio valor, evitando divisão por zero; empates na moda são informados.

## 3. Execução e validação

Na pasta do projeto, execute um dos comandos:

```text
python main.py
python main.py --csv dados/exemplo.csv
python -m unittest discover -s tests -v
```

O programa trata arquivos inválidos, texto em campos numéricos, dados vazios e números não finitos. Foram aprovados 60 testes, com execução também confirmada no GitHub Actions em Python 3.10, 3.12 e 3.13.

**Repositório:** https://github.com/Morenin888/estatistica-python

As referências das funções statistics e da fórmula de Czuber estão no README do repositório.
