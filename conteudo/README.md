# Toolkit Conteúdo (TikTok @joaovictor1639)

Recria, de forma **gratuita e sem IA paga**, as partes determinísticas do bot
**Conteúdo**: fila de vídeos curtos, roteiros de 30–60s, criativo de produto para
o Comércio e uma **agenda de posts espaçados** (nunca em lote).

> **Não publica no TikTok.** Automatizar o app viola os termos. Publicar continua
> **manual e com o seu "ok"**, exatamente como a regra do bot.

## Comandos

```bash
# Gerar um roteiro de 30-60s (gancho / corpo / CTA)
python conteudo/conteudo.py roteiro "3 extensoes do VS Code"

# Criativo de produto (quando o Comércio pedir)
python conteudo/conteudo.py criativo "Kit MagSafe" "iPhone 14"

# Fila de vídeos
python conteudo/conteudo.py fila
python conteudo/conteudo.py add "Setup de home office barato"
python conteudo/conteudo.py status 1 roteiro   # ideia|roteiro|gravado|aprovado|postado

# Agenda de posts (2 ou 3 por semana, espaçados em dias e horas)
python conteudo/conteudo.py agenda --por-semana 3 --semanas 2
```

## Como a agenda funciona

- **3x/semana** → segunda, quarta, sexta. **2x/semana** → terça e quinta.
- Horários alternados (11:00 / 19:00 / 15:00) para **nunca postar em lote**.
- Ignora horários que já passaram e sempre entrega `por_semana × semanas` posts
  **futuros**, puxando os temas da fila (status diferente de `postado`).

## Arquivos

- `conteudo/conteudo.py` — CLI (só biblioteca padrão do Python 3).
- `conteudo/fila.json` — fila de vídeos e a conta do TikTok.
- `conteudo/README.md` — este guia.

Não instala nada e não consome créditos de IA, do Cursor nem do Grok.
