#!/usr/bin/env python3
"""Toolkit do assistente de Carreira do Joao Victor.

Faz as partes legitimas e GRATUITAS do trabalho do bot Carreira:
  - vagas   : busca vagas remotas em APIs publicas (Remotive / RemoteOK)
  - add     : registra uma candidatura no placar (CSV)
  - listar  : lista as candidaturas registradas
  - placar  : resumo das candidaturas por status ("placar de applies")

O que NAO faz (de proposito):
  - Guardar senha do LinkedIn / login automatico / resolver 2FA -> viola os
    termos e e risco de seguranca. Postar no LinkedIn usa a API OFICIAL
    (ver a rotina github_to_linkedin no repo).
  - Enviar candidatura por robo -> continua manual, com o "ok" do Joao.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "candidaturas.csv"
CAMPOS = ["data", "empresa", "vaga", "link", "status"]
REQUEST_TIMEOUT = 25


# --------------------------------------------------------------------------- #
# Busca de vagas
# --------------------------------------------------------------------------- #
def buscar_remotive(termo: str, limite: int) -> list[dict]:
    url = "https://remotive.com/api/remote-jobs"
    resp = requests.get(url, params={"search": termo}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    vagas = []
    for j in resp.json().get("jobs", [])[:limite]:
        vagas.append(
            {
                "fonte": "Remotive",
                "vaga": j.get("title", ""),
                "empresa": j.get("company_name", ""),
                "local": j.get("candidate_required_location", ""),
                "link": j.get("url", ""),
            }
        )
    return vagas


def buscar_remoteok(termo: str, limite: int) -> list[dict]:
    url = "https://remoteok.com/api"
    resp = requests.get(
        url, headers={"User-Agent": "carreira-toolkit/1.0"}, timeout=REQUEST_TIMEOUT
    )
    resp.raise_for_status()
    termo_low = termo.lower()
    vagas = []
    for j in resp.json():
        if "position" not in j:  # primeiro item e metadado
            continue
        texto = f"{j.get('position','')} {j.get('description','')} {' '.join(j.get('tags',[]))}".lower()
        if termo_low and termo_low not in texto:
            continue
        vagas.append(
            {
                "fonte": "RemoteOK",
                "vaga": j.get("position", ""),
                "empresa": j.get("company", ""),
                "local": j.get("location", "") or "Remoto",
                "link": j.get("url", ""),
            }
        )
        if len(vagas) >= limite:
            break
    return vagas


def cmd_vagas(args) -> int:
    fontes = {
        "remotive": [buscar_remotive],
        "remoteok": [buscar_remoteok],
        "todas": [buscar_remotive, buscar_remoteok],
    }[args.fonte]

    todas: list[dict] = []
    for fn in fontes:
        try:
            todas += fn(args.busca, args.limite)
        except requests.RequestException as exc:
            print(f"[aviso] falha em {fn.__name__}: {exc}")

    print(f"== Vagas remotas para '{args.busca}' ({len(todas)} resultado(s)) ==\n")
    for i, v in enumerate(todas, 1):
        print(f"{i:>2}. [{v['fonte']}] {v['vaga']} — {v['empresa']}")
        print(f"    Local: {v['local']}")
        print(f"    Link : {v['link']}\n")
    if not todas:
        print("Nenhuma vaga encontrada. Tente outro termo de busca.")
    return 0


# --------------------------------------------------------------------------- #
# Placar de candidaturas
# --------------------------------------------------------------------------- #
def ler_candidaturas() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escrever_candidaturas(linhas: list[dict]) -> None:
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(linhas)


def cmd_add(args) -> int:
    linhas = ler_candidaturas()
    linhas.append(
        {
            "data": date.today().isoformat(),
            "empresa": args.empresa,
            "vaga": args.vaga,
            "link": args.link or "",
            "status": args.status,
        }
    )
    escrever_candidaturas(linhas)
    print(f"[ok] candidatura registrada: {args.empresa} — {args.vaga} ({args.status})")
    return 0


def cmd_listar(args) -> int:
    linhas = ler_candidaturas()
    if not linhas:
        print("Nenhuma candidatura registrada ainda. Use 'add' para incluir.")
        return 0
    print(f"== Candidaturas ({len(linhas)}) ==\n")
    for c in linhas:
        print(f"- {c['data']} | {c['empresa']} — {c['vaga']} [{c['status']}]")
        if c["link"]:
            print(f"    {c['link']}")
    return 0


def cmd_placar(args) -> int:
    linhas = ler_candidaturas()
    print("== Placar de candidaturas (modo economia) ==\n")
    print(f"Total: {len(linhas)}")
    if not linhas:
        return 0
    contagem: dict[str, int] = {}
    for c in linhas:
        contagem[c["status"]] = contagem.get(c["status"], 0) + 1
    for status, n in sorted(contagem.items(), key=lambda x: -x[1]):
        print(f"  {status:<12}: {n}")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Toolkit do assistente de Carreira")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pv = sub.add_parser("vagas", help="busca vagas remotas em APIs publicas")
    pv.add_argument("busca", help="termo de busca (ex.: python, react, dados)")
    pv.add_argument("--limite", type=int, default=10, help="max de vagas por fonte")
    pv.add_argument(
        "--fonte", choices=["remotive", "remoteok", "todas"], default="remotive"
    )

    pa = sub.add_parser("add", help="registra uma candidatura")
    pa.add_argument("empresa")
    pa.add_argument("vaga")
    pa.add_argument("--link", default="")
    pa.add_argument("--status", default="aplicado")

    sub.add_parser("listar", help="lista as candidaturas")
    sub.add_parser("placar", help="resumo por status")

    args = parser.parse_args()
    comandos = {
        "vagas": cmd_vagas,
        "add": cmd_add,
        "listar": cmd_listar,
        "placar": cmd_placar,
    }
    return comandos[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
