#!/usr/bin/env python3
"""Toolkit do assistente de E-mails do Joao Victor (Gmail).

Faz a triagem da caixa pela API OFICIAL do Gmail:
  - triagem : classifica os e-mails (protegido / vaga / precisa resposta / ruido)
  - rascunho: cria um rascunho de resposta (NAO envia)

Regra de ouro (igual ao bot original):
  - NUNCA envia nem apaga automaticamente.
  - Arquivar ruido so acontece com a flag --aplicar (acao reversivel).
  - Enviar e apagar continuam manuais, com o "ok" explicito do Joao.

Sem credenciais do Gmail, use 'triagem --demo' para ver a logica funcionando
com e-mails de exemplo (emails/exemplos.json).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
REGRAS_PATH = BASE / "regras.json"
EXEMPLOS_PATH = BASE / "exemplos.json"

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
REQUEST_TIMEOUT = 25

PROTEGIDO, VAGA, PRECISA_RESPOSTA, RUIDO = (
    "PROTEGIDO",
    "VAGA",
    "PRECISA_RESPOSTA",
    "RUIDO",
)


# --------------------------------------------------------------------------- #
# Classificacao (deterministica, sem IA)
# --------------------------------------------------------------------------- #
def carregar_regras() -> dict:
    return json.loads(REGRAS_PATH.read_text(encoding="utf-8"))


def _bate(texto: str, termos: list[str]) -> bool:
    return any(t in texto for t in termos)


def classificar(msg: dict, regras: dict) -> str:
    texto = f"{msg.get('from', '')} {msg.get('subject', '')}".lower()
    if _bate(texto, regras["manter_visivel"]):
        return PROTEGIDO
    if _bate(texto, regras["vaga_keywords"]):
        return VAGA
    if _bate(texto, regras["ruido_keywords"]):
        return RUIDO
    return PRECISA_RESPOSTA


# --------------------------------------------------------------------------- #
# Cliente Gmail (API oficial)
# --------------------------------------------------------------------------- #
def get_access_token() -> str:
    data = {
        "client_id": os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }
    resp = requests.post(OAUTH_TOKEN_URL, data=data, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def listar_mensagens(token: str, query: str, limite: int) -> list[dict]:
    resp = requests.get(
        f"{GMAIL_API}/messages",
        headers=_headers(token),
        params={"q": query, "maxResults": limite},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    ids = [m["id"] for m in resp.json().get("messages", [])]
    mensagens = []
    for mid in ids:
        det = requests.get(
            f"{GMAIL_API}/messages/{mid}",
            headers=_headers(token),
            params={"format": "metadata", "metadataHeaders": ["From", "Subject"]},
            timeout=REQUEST_TIMEOUT,
        )
        det.raise_for_status()
        d = det.json()
        headers = {h["name"].lower(): h["value"] for h in d["payload"]["headers"]}
        mensagens.append(
            {
                "id": mid,
                "from": headers.get("from", ""),
                "subject": headers.get("subject", ""),
                "snippet": d.get("snippet", ""),
            }
        )
    return mensagens


def arquivar(token: str, msg_id: str) -> None:
    """Remove o rotulo INBOX (arquiva, sem apagar). Acao reversivel."""
    requests.post(
        f"{GMAIL_API}/messages/{msg_id}/modify",
        headers={**_headers(token), "Content-Type": "application/json"},
        json={"removeLabelIds": ["INBOX"]},
        timeout=REQUEST_TIMEOUT,
    ).raise_for_status()


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #
def _coletar_mensagens(args, token: str | None) -> list[dict]:
    if args.demo:
        return json.loads(EXEMPLOS_PATH.read_text(encoding="utf-8"))
    return listar_mensagens(token, args.query, args.limite)


def cmd_triagem(args) -> int:
    regras = carregar_regras()
    token = None if args.demo else get_access_token()
    mensagens = _coletar_mensagens(args, token)

    grupos: dict[str, list[dict]] = {
        PROTEGIDO: [],
        VAGA: [],
        PRECISA_RESPOSTA: [],
        RUIDO: [],
    }
    for m in mensagens:
        grupos[classificar(m, regras)].append(m)

    print("== Triagem de e-mails (modo economia) ==\n")
    print(f"Total analisado : {len(mensagens)}")
    print(f"Protegidos      : {len(grupos[PROTEGIDO])}")
    print(f"Vagas           : {len(grupos[VAGA])}")
    print(f"Precisa resposta: {len(grupos[PRECISA_RESPOSTA])}")
    print(f"Ruido           : {len(grupos[RUIDO])}\n")

    if grupos[PRECISA_RESPOSTA]:
        print("PRECISA DE RESPOSTA (prioridade):")
        for m in grupos[PRECISA_RESPOSTA]:
            print(f"  - {m['from']} | {m['subject']}")
    if grupos[VAGA]:
        print("\nAVISAR CARREIRA (parece vaga):")
        for m in grupos[VAGA]:
            print(f"  - {m['from']} | {m['subject']}")
    if grupos[PROTEGIDO]:
        print("\nMANTIDOS VISIVEIS:")
        for m in grupos[PROTEGIDO]:
            print(f"  - {m['from']} | {m['subject']}")
    if grupos[RUIDO]:
        print("\nRUIDO (sugestao: arquivar):")
        for m in grupos[RUIDO]:
            print(f"  - {m['from']} | {m['subject']}")

    if args.aplicar and not args.demo:
        print("\nArquivando ruido (acao reversivel)...")
        for m in grupos[RUIDO]:
            arquivar(token, m["id"])
            print(f"  [arquivado] {m['subject']}")
    elif args.aplicar and args.demo:
        print("\n[demo] --aplicar ignorado no modo demo.")
    else:
        print("\n(nada foi alterado. Use --aplicar para arquivar o ruido.)")

    print("\nEnviar/apagar exigem o OK do Joao (nunca automatico).")
    return 0


def cmd_rascunho(args) -> int:
    token = get_access_token()
    import base64
    from email.mime.text import MIMEText

    mime = MIMEText(args.corpo)
    mime["To"] = args.para
    mime["Subject"] = args.assunto
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()

    resp = requests.post(
        f"{GMAIL_API}/drafts",
        headers={**_headers(token), "Content-Type": "application/json"},
        json={"message": {"raw": raw}},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    print(f"[ok] rascunho criado (id: {resp.json().get('id')}). NAO foi enviado.")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Toolkit do assistente de E-mails")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pt = sub.add_parser("triagem", help="classifica os e-mails da caixa")
    pt.add_argument("--demo", action="store_true", help="usa e-mails de exemplo")
    pt.add_argument("--query", default="in:inbox is:unread", help="filtro de busca Gmail")
    pt.add_argument("--limite", type=int, default=25)
    pt.add_argument("--aplicar", action="store_true", help="arquiva o ruido (reversivel)")

    pr = sub.add_parser("rascunho", help="cria um rascunho de resposta (nao envia)")
    pr.add_argument("--para", required=True)
    pr.add_argument("--assunto", required=True)
    pr.add_argument("--corpo", required=True)

    args = parser.parse_args()
    comandos = {"triagem": cmd_triagem, "rascunho": cmd_rascunho}
    return comandos[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
