# Rotina: GitHub → LinkedIn

Automação que **verifica seus repositórios no GitHub**, **elabora um post de divulgação**
de cada projeto e **publica no LinkedIn** usando a **API oficial** (escopo
`w_member_social`).

> Importante: esta rotina usa **somente APIs oficiais** e um token que você mesmo
> gera. Ela **não** automatiza login de navegador nem quebra de CAPTCHA — isso
> viola os termos do LinkedIn e pode banir a sua conta.

## Como funciona

1. Busca seus repositórios na API pública do GitHub (`/users/<você>/repos`).
2. Filtra projetos relevantes (ignora forks, repositórios arquivados, o repo do
   próprio perfil e os que já foram divulgados).
3. Monta um texto profissional em português (nome, descrição, stack, link e hashtags).
4. Publica no LinkedIn e registra o repositório em `automation/state/posted.json`
   para **não repetir** na próxima rodada.

Sem token do LinkedIn, ele roda em **modo dry-run**: apenas mostra o texto que
seria publicado (ótimo para testar).

## Rodar localmente

```bash
pip install -r automation/requirements.txt

# Só testar (dry-run), sem publicar:
GITHUB_USERNAME=dev-joaovictor python automation/github_to_linkedin.py

# Publicar de verdade:
export LINKEDIN_ACCESS_TOKEN="seu_token"
export GITHUB_USERNAME="dev-joaovictor"
export DRY_RUN=false
python automation/github_to_linkedin.py
```

## Variáveis de configuração

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `GITHUB_USERNAME` | não | `dev-joaovictor` | Usuário do GitHub a consultar. |
| `LINKEDIN_ACCESS_TOKEN` | para publicar | — | Token OAuth do LinkedIn com escopo `w_member_social`. |
| `LINKEDIN_AUTHOR_URN` | não | resolvido automaticamente | Ex.: `urn:li:person:XXXX`. Se vazio, é obtido via `/v2/userinfo`. |
| `GH_API_TOKEN` | não | — | Token do GitHub (aumenta o limite de requisições). |
| `MAX_POSTS` | não | `1` | Máximo de projetos publicados por rodada. |
| `MIN_STARS` | não | `0` | Só publica repos com pelo menos N estrelas. |
| `INCLUDE_FORKS` | não | `false` | Incluir forks. |
| `SKIP_REPOS` | não | — | Lista separada por vírgula de repos a ignorar. |
| `DRY_RUN` | não | `true` se não houver token | `true` = não publica. |
| `STATE_FILE` | não | `automation/state/posted.json` | Onde guardar o histórico. |

## Como gerar o token do LinkedIn (uma vez)

1. Acesse o [LinkedIn Developers](https://www.linkedin.com/developers/apps) e crie um app.
2. No app, adicione o produto **"Share on LinkedIn"** (concede o escopo `w_member_social`)
   e **"Sign In with LinkedIn using OpenID Connect"** (concede `openid profile`,
   usados para descobrir seu URN automaticamente).
3. Gere um **access token** com os escopos `w_member_social openid profile`
   (pelo fluxo OAuth 2.0 do próprio painel ou pela ferramenta de token do LinkedIn).
4. Guarde o token — ele é usado na variável `LINKEDIN_ACCESS_TOKEN`.

> Tokens do LinkedIn costumam expirar em ~60 dias. Quando expirar, gere um novo
> e atualize o secret.

## Rodar automaticamente (GitHub Actions)

Já existe o workflow [`.github/workflows/github-linkedin.yml`](../.github/workflows/github-linkedin.yml),
que roda **toda segunda-feira às 12:00 UTC** (ou manualmente pela aba **Actions**).

Configure em **Settings → Secrets and variables → Actions**:

- **Secrets**
  - `LINKEDIN_ACCESS_TOKEN` — obrigatório para publicar.
  - `LINKEDIN_AUTHOR_URN` — opcional (o script resolve sozinho se faltar).
- **Variables** (opcional)
  - `GITHUB_USERNAME`, `MAX_POSTS`.

Para testar sem publicar: aba **Actions → Divulgar projetos no LinkedIn → Run workflow**
e deixe a opção **dry_run** marcada.

## Rodar como Automação do Cursor (alternativa)

Em vez do GitHub Actions, você pode usar as **Automations** do Cursor
([cursor.com/automations](https://cursor.com/automations)): crie uma automação
com gatilho agendado que rode `python automation/github_to_linkedin.py` neste
repositório, com o `LINKEDIN_ACCESS_TOKEN` nos secrets do ambiente.
