# Toolkit Carreira

Recria, de forma **legítima e gratuita**, as partes automatizáveis do bot
**Carreira**: busca de **vagas remotas** e controle do **placar de candidaturas**.

## O que NÃO é automatizado (e por quê)

- **Senha do LinkedIn / login automático / 2FA**: não guardamos senha nem
  automatizamos login. Isso viola os termos do LinkedIn, pode banir sua conta e é
  um risco de segurança. Para **postar** no LinkedIn, use a API oficial (ver a
  rotina `github_to_linkedin` no repositório).
- **Enviar candidatura por robô**: continua **manual e com o seu "ok"**, igual à
  regra do bot.

## Comandos

```bash
pip install -r carreira/requirements.txt

# Buscar vagas remotas (fonte padrão: Remotive)
python carreira/carreira.py vagas python --limite 5
python carreira/carreira.py vagas react --fonte todas   # Remotive + RemoteOK

# Registrar uma candidatura no placar
python carreira/carreira.py add "BairesDev" "Python Developer" --link URL --status aplicado

# Ver as candidaturas e o placar por status
python carreira/carreira.py listar
python carreira/carreira.py placar
```

Status sugeridos: `aplicado`, `entrevista`, `teste`, `oferta`, `recusado`.

## Fontes de vagas (APIs públicas e gratuitas)

- **Remotive** — `https://remotive.com/api/remote-jobs`
- **RemoteOK** — `https://remoteok.com/api`

## Onde ficam os dados

As candidaturas são salvas em `carreira/candidaturas.csv` (colunas:
`data, empresa, vaga, link, status`). É um arquivo simples que você pode abrir no
Excel/Google Sheets.
