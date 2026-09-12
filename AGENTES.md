# Empresa de Agentes do João Victor

Reconstrução, em código aberto e **gratuito**, do time de agentes que rodava no
Grok Bot. Tudo funciona sem consumir créditos de IA (nem do Cursor, nem do Grok):
são scripts em Python + APIs oficiais + GitHub Actions.

## Organograma

```
                 Gerente (coordena, sob demanda)
    ┌───────────┬───────────┬───────────┬───────────┐
  Código     Conteúdo    Carreira    Comércio     E-mails
```

| Bot | Pasta | O que faz |
|---|---|---|
| **Gerente** | `gerente/` | Coordena; acorda um bot sob demanda (sem fan-out) |
| **Código** | `codigo/` | PRs, CI, reviews e status de merge (GitHub API) |
| **Conteúdo** | `conteudo/` | Roteiros 30–60s, fila de vídeos e agenda de posts |
| **Carreira** | `carreira/` | Vagas remotas + placar de candidaturas |
| **Comércio** | `comercio/` | Catálogo, precificação Shopee, busca de fornecedor, relatório |
| **E-mails** | `emails/` | Triagem do Gmail, rascunhos (nunca envia sozinho) |
| **Divulgação** | `automation/` | GitHub → LinkedIn (API oficial), agendado — via `gerente divulgacao rodar` |

Utilitário compartilhado: `common/web.py` — dá a **todos os bots** acesso à
internet (busca e leitura de páginas).

## Ponto de entrada: o Gerente

```bash
python gerente/gerente.py bots                       # lista os bots
python gerente/gerente.py carreira vagas python --fonte web
python gerente/gerente.py codigo relatorio
python gerente/gerente.py conteudo agenda --por-semana 3 --semanas 2
python gerente/gerente.py comercio fornecedor --sku MAG-KIT-14
python gerente/gerente.py emails triagem --demo
python gerente/gerente.py divulgacao rodar           # dry-run sem token LinkedIn
python gerente/gerente.py web buscar "kit magsafe fornecedor"
```

## O "computador virtual" de cada bot

No Cursor, cada **Cloud Agent / Automação roda na sua própria VM isolada**, com
internet. O arquivo [`.cursor/environment.json`](.cursor/environment.json) define
esse computador virtual (instala as dependências de `requirements.txt`). Assim,
para dar "um computador para cada bot", basta rodar cada bot como sua própria
**Automação** em [cursor.com/automations](https://cursor.com/automations):

- Cada automação = uma VM própria, com internet, agendada (cron) ou por evento.
- Ex.: uma automação diária para o `emails triagem`, uma semanal para o
  `carreira vagas`, outra para a divulgação `GitHub → LinkedIn`.

Todos os bots já usam `requests` para acessar a internet, e `common/web.py`
adiciona busca (DuckDuckGo) e leitura de páginas.

## Acesso à internet — busca e leitura

```bash
python common/web.py buscar "vagas python remoto"
python common/web.py fetch https://example.com
```

## Credenciais (só onde precisa publicar/ler conta)

- **LinkedIn** (divulgação): `LINKEDIN_ACCESS_TOKEN` — ver `automation/README.md`.
- **Gmail** (e-mails): `GMAIL_CLIENT_ID/SECRET/REFRESH_TOKEN` — ver `emails/README.md`.
- **GitHub** (código): `GH_API_TOKEN` opcional — ver `codigo/README.md`.

## Regras de ouro (herdadas dos bots)

- Só **publica/envia/gasta/apaga** com o **"ok" explícito do João**.
- **Nada** de burlar login/CAPTCHA — só APIs oficiais (não banir contas).
- Modo economia: cada bot reporta só **resultado ou bloqueio**.
