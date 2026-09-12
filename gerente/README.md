# Gerente geral (enxuto)

Coordena os bots da Empresa de Agentes a partir de um único ponto de entrada.

## Princípio: economia de crédito

- **Sem fan-out** — nunca roda todos os bots de uma vez.
- **Sem panorama automático** — não gera relatório geral sozinho.
- **Sob demanda** — acorda só o bot que você pedir e sobe apenas resultado/bloqueio.

## Uso

```bash
python gerente/gerente.py bots

python gerente/gerente.py carreira placar
python gerente/gerente.py codigo relatorio
python gerente/gerente.py conteudo agenda --por-semana 3 --semanas 2
python gerente/gerente.py emails triagem --demo
python gerente/gerente.py comercio fornecedor --sku MAG-KIT-14
python gerente/gerente.py divulgacao rodar
python gerente/gerente.py web buscar "kit magsafe fornecedor"
```

O Gerente apenas **repassa** o comando para o bot certo e mostra a saída dele
(que já vem em "modo economia"). Ele não interpreta nem resume — mantém enxuto.

## Bots coordenados

| Bot | Script | Faz |
|---|---|---|
| `codigo` | `codigo/codigo.py` | PRs, CI, reviews e status de merge |
| `conteudo` | `conteudo/conteudo.py` | roteiros, fila e agenda de posts |
| `carreira` | `carreira/carreira.py` | vagas remotas e placar de candidaturas |
| `comercio` | `comercio/comercio.py` | catálogo, precificação, fornecedor e relatório |
| `emails` | `emails/triagem.py` | triagem do Gmail e rascunhos |
| `divulgacao` | `automation/github_to_linkedin.py` | GitHub → LinkedIn (dry-run sem token) |
| `web` | `common/web.py` | busca e leitura de páginas |

## Importante

O Gerente só consegue acordar um bot se o script dele existir no repo. Se estiver
ausente, `gerente bots` mostra `AUSENTE` e o comando retorna bloqueio claro.
