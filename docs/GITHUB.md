# Publicação no GitHub

O nome sugerido para o repositório é `estatistica-python`. A publicação usa a conta do integrante responsável; este documento não pressupõe que o repositório já exista.

## Opção 1 — pelo navegador

1. Entre na sua conta em <https://github.com> e abra <https://github.com/new>.
2. Selecione sua própria conta como proprietário e use o nome `estatistica-python`. Se esse nome já existir na conta, confirme se aquele é o repositório destinado a este trabalho antes de adicionar arquivos; escolha outro nome se for um projeto diferente.
3. Crie inicialmente um repositório privado. Não marque as opções para gerar README, `.gitignore` ou licença: esses arquivos do projeto serão enviados junto com o código.
4. Abra **Add file → Upload files**. Arraste o conteúdo da pasta `estatistica-python`, mantendo as pastas `estatistica`, `dados`, `docs`, `tests` e `.github`. Envie também `main.py`, `README.md` e `.gitignore`. Arquivos iniciados por ponto podem estar ocultos no gerenciador de arquivos; habilite sua exibição para incluir `.github` e `.gitignore`. Não envie a pasta local `.git`, se houver, nem ambientes virtuais ou caches.
5. Confirme os arquivos e registre o envio com uma mensagem como `Adiciona analisador estatístico, exemplos e relatório`.
6. Confira que o README aparece na página inicial, que `docs/relatorio.pdf` abre e que a aba **Actions** apresenta a execução dos testes. A primeira execução pode demorar alguns minutos.
7. Se o professor exigir acesso público, use **Settings → General → Danger Zone → Change repository visibility** para tornar o repositório público. Se aceitar privado, conceda acesso ao professor pelo usuário GitHub que ele informar, em **Settings → Collaborators**.
8. Entregue a URL copiada da página do repositório e o PDF solicitado. Os quatro integrantes estão identificados no README e no relatório.

Não inclua senhas ou tokens em arquivos, commits ou mensagens. A autenticação deve acontecer no próprio GitHub ou no fluxo oficial do GitHub CLI.

## Opção 2 — Git e GitHub CLI no seu computador

Requisitos: Git e [GitHub CLI](https://cli.github.com/) instalados. Abra um terminal dentro da pasta do projeto. Autentique pela janela do navegador e confirme qual conta está ativa:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth status
git status
```

Se `git status` indicar que a pasta ainda não é um repositório, inicialize:

```bash
git init -b main
```

Use a sua identidade real de autor, caso o Git solicite nome e e-mail. Em seguida, revise o conteúdo e crie o commit:

```bash
git add .
git diff --cached --stat
git status
git commit -m "Adiciona analisador estatístico, exemplos e relatório"
```

Antes de criar o repositório, confirme no navegador que `estatistica-python` ainda não existe na conta autenticada. O comando abaixo cria um repositório privado nessa conta e envia o projeto:

```bash
gh repo create estatistica-python --private --source=. --remote=origin --push
gh repo view --web
```

Se a pasta já possuir um remoto `origin`, confira-o antes de publicar:

```bash
git remote -v
```

Se o repositório de destino já existir, use o histórico dele como base e adicione os arquivos do projeto em um clone, após revisar os arquivos existentes. Não execute `git push --force`, não apague o histórico e não substitua um repositório de outro trabalho. Registre e envie as mudanças normalmente com `git add`, `git commit` e `git push`.

## Conferência da entrega

- README e nomes dos integrantes conferidos.
- Código-fonte, exemplos CSV, testes e relatório PDF disponíveis.
- Testes locais aprovados e execução do GitHub Actions verificada.
- Acesso do professor definido conforme o formato de entrega.
- URL real do repositório copiada para a submissão.

Os commits devem refletir quem realizou cada alteração. A lista de integrantes identifica o grupo e não atribui participação histórica ou contas GitHub individuais.
