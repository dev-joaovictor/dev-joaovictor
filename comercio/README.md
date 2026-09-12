# Toolkit Comércio (Kits MagSafe)

Recria, de forma **gratuita e sem IA paga**, as partes determinísticas do antigo
bot **Comércio** (dropshipping de Kits MagSafe para iPhone 13/14/15): catálogo,
precificação com taxas da Shopee, relatório em "modo economia" e brief de criativo.

> O que **não** é automatizado: publicar produto na Shopee/TikTok Shop e gastar
> dinheiro. Isso continua **manual e depende do seu "ok"** — tanto pela regra do
> bot quanto porque automatizar login/navegação nesses sites viola os termos.

## Arquivos

- `config.json` — taxas da Shopee e margem alvo padrão (edite conforme as taxas atuais).
- `catalogo.json` — seus produtos (preencha `custo_fornecedor` e `link_fornecedor`).
- `comercio.py` — CLI com os comandos abaixo.

## Comandos

```bash
# Preço de venda para bater a margem alvo (usa o catalogo.json)
python comercio/comercio.py precificar

# Lucro/margem a partir de um preço de venda específico
python comercio/comercio.py lucro --custo 22.50 --preco 47.32

# Resumo "modo economia": prontos x bloqueios (o que falta preencher)
python comercio/comercio.py relatorio

# Brief de criativo para mandar ao time de Conteúdo
python comercio/comercio.py brief MAG-KIT-14
```

## Como a precificação funciona

Dado o custo do fornecedor, a margem alvo e as taxas da Shopee, o preço de venda é:

```
preço = (custo + taxa_fixa) / (1 - comissão% - margem_alvo)
```

Assim o preço sugerido já **garante a margem** depois de descontar a comissão e a
taxa fixa por item da Shopee.

> Importante: **confirme as taxas atuais da Shopee** em `config.json`
> (`comissao_pct`, `taxa_fixa_por_item`). Elas mudam com o tempo e por programa
> (ex.: Programa de Frete Grátis).

## Sem dependências extras

Usa só a biblioteca padrão do Python 3 — não precisa instalar nada e não consome
créditos de IA nem do Cursor.
