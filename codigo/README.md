# Toolkit Código (Engenharia + GitHub)

Recria a parte de monitoramento do bot **Código** (que absorveu o bot GitHub):
acompanha **PRs, CI, reviews e status de merge** via API oficial do GitHub, e
reporta em **modo economia** só o que está **pronto para merge** ou **bloqueado**.

> As tarefas de código em si (features, bugs, refactors) são feitas por um
> **Cloud Agent do Cursor**. Este toolkit cobre o acompanhamento do GitHub, que é
> determinístico e gratuito.

## Comandos

```bash
pip install -r codigo/requirements.txt

# Tabela de PRs abertos com CI, review e status de merge
python codigo/codigo.py prs

# Modo economia: só o que precisa de ação (pronto p/ merge x bloqueios)
python codigo/codigo.py relatorio

# Apontar para outro repositório
python codigo/codigo.py --repo owner/repo prs
```

## Como cada PR é classificado

- **PRONTO** — não é draft, review **aprovado**, CI **verde** (ou sem CI) e sem
  conflito de merge. Aparece como "precisa do OK do João".
- **BLOQUEADO** — CI **vermelho**, **mudanças solicitadas** ou **conflito de merge**.
- **ANDAMENTO** — draft, sem review ainda, ou CI pendente.

## Configuração

- **Repositório**: `--repo owner/repo`, ou a variável `GITHUB_REPO`, ou detectado
  automaticamente do `git remote`.
- **Token** (opcional em repo público, recomendado para evitar limite de
  requisições): `GH_API_TOKEN` ou `GITHUB_TOKEN`.

```bash
export GH_API_TOKEN="seu_token_github"
```

## Fora de escopo

Não faz LinkedIn, vagas, TikTok nem comércio (isso é dos outros toolkits).
Fazer o merge continua **manual, com o "ok" do João**.
