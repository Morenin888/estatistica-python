# Repositório no GitHub

O repositório do trabalho foi criado na conta **Morenin888**:

<https://github.com/Morenin888/estatistica-python>

Ele é **privado**. O estado da publicação dos arquivos e da verificação do GitHub Actions está registrado no [checklist](CHECKLIST.md). A criação do repositório não confirma, por si só, o envio dos arquivos ou a submissão ao professor.

## Baixar e executar

É necessário Python 3.10 ou superior. A aplicação não exige pacotes externos.

Para acessar um repositório privado, autentique uma conta que tenha acesso a ele. Com [GitHub CLI](https://cli.github.com/) e Git instalados:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth status
gh repo clone Morenin888/estatistica-python
cd estatistica-python
python main.py
```

Se o Git já estiver autenticado, também é possível clonar diretamente:

```bash
git clone https://github.com/Morenin888/estatistica-python.git
cd estatistica-python
```

Para executar um exemplo e conferir os testes, dentro da pasta do projeto:

```bash
python main.py --csv dados/exemplo.csv
python -m unittest discover -s tests -v
```

Os demais comandos estão no [README](../README.md). O relatório fica em [docs/relatorio.pdf](relatorio.pdf). Pelo navegador, também é possível usar **Code → Download ZIP** na página do repositório, quando os arquivos estiverem publicados e sua conta tiver acesso.

## Atualizar o projeto

Use um clone do repositório existente para preservar seu histórico. Antes de editar, confira o remoto e sincronize a cópia local:

```bash
git remote -v
git status
git pull --ff-only
```

Após realizar as alterações, execute os testes e revise o que será enviado:

```bash
python -m unittest discover -s tests -v
git diff
git add .
git diff --cached --stat
git status
git commit -m "Atualiza analisador estatístico e documentação"
git push
```

O remoto deve apontar para `Morenin888/estatistica-python`. Caso haja mudanças locais ou conflitos, revise-os antes de sincronizar; não apague o histórico nem execute `git push --force`. Use sua identidade real de autor se o Git solicitar nome e e-mail. A lista de integrantes identifica o grupo e não atribui contas individuais, funções ou participação histórica nos commits.

Para uma edição pequena pelo navegador, abra o arquivo no repositório e use o botão de edição. Para adicionar arquivos, use **Add file → Upload files**, preservando as pastas do projeto. Confira sempre o conteúdo antes de registrar o commit.

## Conferir a publicação

1. Abra <https://github.com/Morenin888/estatistica-python> com uma conta autorizada.
2. Confira se o README aparece e se código, exemplos CSV, testes e `docs/relatorio.pdf` estão disponíveis.
3. Abra a aba **Actions** e confira o resultado do workflow **Testes** para o commit publicado. Ele executa a suíte e um exemplo CSV em Python 3.10, 3.12 e 3.13.
4. Marque as etapas correspondentes no [checklist](CHECKLIST.md) somente depois da confirmação.

## Acesso do professor e submissão

Como o repositório é privado, o professor precisa receber acesso. Se ele aceitar repositórios privados, solicite seu nome de usuário GitHub e conceda acesso em **Settings → Collaborators**. A aceitação do convite também deve ser conferida.

Se a orientação da disciplina exigir repositório público, o proprietário pode alterar a visibilidade em **Settings → General → Danger Zone → Change repository visibility**. A criação deste projeto privado não confirma essa alteração nem o acesso do professor.

Entregue a URL <https://github.com/Morenin888/estatistica-python> e o arquivo `docs/relatorio.pdf` pelo canal indicado pelo professor, até **10 de outubro de 2026**. Confirme o envio antes de marcar a submissão no checklist.
