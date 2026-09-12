# Toolkit E-mails (Gmail)

Recria o bot **E-mails** (Gmail `joaovictortrabalho084`): faz a **triagem** da
caixa, separa **ruído** do que **precisa de resposta**, mantém visíveis os
remetentes importantes e avisa o **Carreira** quando é vaga — tudo pela **API
oficial do Gmail**.

## Regra de ouro (segurança)

- **Nunca envia nem apaga automaticamente.**
- **Arquivar ruído** só com a flag `--aplicar` (ação **reversível** — só tira da
  caixa de entrada, não deleta).
- **Enviar e apagar** continuam **manuais, com o seu "ok"**.
- Rascunhos são criados como **rascunho** (não são enviados).

## Comandos

```bash
pip install -r emails/requirements.txt

# Ver a triagem SEM tocar na caixa (com e-mails de exemplo):
python emails/triagem.py triagem --demo

# Triagem real (precisa das credenciais do Gmail — ver abaixo):
python emails/triagem.py triagem

# Triagem real e arquivar o ruído (reversível):
python emails/triagem.py triagem --aplicar

# Criar um rascunho de resposta (NÃO envia):
python emails/triagem.py rascunho --para "pessoa@x.com" --assunto "Re: assunto" --corpo "Texto"
```

## Categorias da triagem

- **PROTEGIDO** — mantidos visíveis (MixRank, Hire Feed, Erick Carlos, alertas de
  segurança). Configurável em `emails/regras.json`.
- **VAGA** — parece oportunidade de emprego → "avisar Carreira".
- **PRECISA_RESPOSTA** — e-mails diretos que pedem retorno (prioridade).
- **RUÍDO** — newsletters/promoções → sugestão de arquivar.

Edite as listas de palavras-chave em `emails/regras.json`.

## Configurar o acesso ao Gmail (uma vez)

1. No [Google Cloud Console](https://console.cloud.google.com/), crie um projeto
   e ative a **Gmail API**.
2. Crie credenciais **OAuth 2.0 (Desktop app)** → você recebe `client_id` e
   `client_secret`.
3. Autorize o escopo `https://www.googleapis.com/auth/gmail.modify` e gere um
   **refresh token** (pelo [OAuth Playground](https://developers.google.com/oauthplayground/)
   ou por um script de consentimento).
4. Defina as variáveis de ambiente:

```bash
export GMAIL_CLIENT_ID="..."
export GMAIL_CLIENT_SECRET="..."
export GMAIL_REFRESH_TOKEN="..."
```

> Use `gmail.modify` (permite arquivar e criar rascunhos) — **não** é preciso o
> escopo de envio, já que o toolkit nunca envia sozinho.

## Rodar automático

Pode agendar via GitHub Actions (com os 3 secrets acima) ou como Automação do
Cursor, rodando `python emails/triagem.py triagem` no horário que quiser. Deixe o
`--aplicar` de fora até confiar na triagem.
