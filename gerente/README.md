# Gerente geral (enxuto)

Coordena os bots **Código, Conteúdo, Carreira, Comércio e E-mails** a partir de um
único ponto de entrada.

## Princípio: economia de crédito

- **Sem fan-out** — nunca roda todos os bots de uma vez.
- **Sem panorama automático** — não gera relatório geral sozinho.
- **Sob demanda** — acorda só o bot que você pedir e sobe apenas resultado/bloqueio.

## Uso

```bash
# Ver os bots e o que cada um faz (e se estão presentes no repo)
python gerente/gerente.py bots

# Acordar SÓ um bot, sob demanda, repassando o comando dele
python gerente/gerente.py carreira placar
python gerente/gerente.py codigo relatorio
python gerente/gerente.py conteudo agenda --por-semana 3 --semanas 2
python gerente/gerente.py emails triagem --demo
python gerente/gerente.py comercio precificar
```

O Gerente apenas **repassa** o comando para o bot certo e mostra a saída dele
(que já vem em "modo economia"). Ele não interpreta nem resume — mantém enxuto.

## Bots coordenados

| Bot | Script | Faz |
|---|---|---|
| `codigo` | `codigo/codigo.py` | PRs, CI, reviews e status de merge |
| `conteudo` | `conteudo/conteudo.py` | roteiros, fila e agenda de posts |
| `carreira` | `carreira/carreira.py` | vagas remotas e placar de candidaturas |
| `comercio` | `comercio/comercio.py` | catálogo, precificação e relatório |
| `emails` | `emails/triagem.py` | triagem do Gmail e rascunhos |

## Importante

Cada bot vive em seu próprio diretório (e foi entregue em um PR separado). O
Gerente só consegue acordar um bot se o diretório dele estiver presente no repo.
Depois de fazer o **merge dos PRs dos bots** na `main`, o Gerente coordena todos.
Enquanto um bot estiver ausente, `gerente bots` mostra o status `AUSENTE` e o
comando retorna um bloqueio claro.
