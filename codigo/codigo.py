#!/usr/bin/env python3
"""Toolkit do assistente de Engenharia (Codigo + GitHub) do Joao Victor.

Absorveu o bot GitHub: acompanha PRs, CI, reviews e status de merge.
  - prs       : lista os PRs abertos com CI, review e status de merge
  - relatorio : modo economia -> so o que esta PRONTO p/ merge ou BLOQUEADO

As tarefas de codigo em si (features, bugs, refactors) sao feitas por um Cloud
Agent do Cursor. Este toolkit cobre a parte de monitoramento do GitHub, que e
deterministica e gratuita (API oficial do GitHub).

Repo: definido por --repo, ou env GITHUB_REPO (owner/repo), ou detectado do
remote git. Token: env GH_API_TOKEN ou GITHUB_TOKEN (opcional em repo publico).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

import requests

API = "https://api.github.com"
REQUEST_TIMEOUT = 25


# --------------------------------------------------------------------------- #
def detectar_repo() -> str:
    if os.getenv("GITHUB_REPO"):
        return os.environ["GITHUB_REPO"]
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        raise SystemExit("Nao consegui detectar o repo. Use --repo owner/repo.")
    m = re.search(r"github\.com[:/](.+?/.+?)(?:\.git)?$", url)
    if not m:
        raise SystemExit(f"Remote nao reconhecido: {url}. Use --repo owner/repo.")
    return m.group(1)


def token() -> str:
    return os.getenv("GH_API_TOKEN") or os.getenv("GITHUB_TOKEN") or ""


def get(path: str) -> object:
    headers = {"Accept": "application/vnd.github+json"}
    tok = token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    resp = requests.get(f"{API}{path}", headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# --------------------------------------------------------------------------- #
def status_ci(repo: str, sha: str) -> str:
    """verde | vermelho | pendente | sem CI"""
    data = get(f"/repos/{repo}/commits/{sha}/check-runs")
    runs = data.get("check_runs", [])
    if not runs:
        # fallback para o status legado (commit statuses).
        # A API combinada retorna state="pending" mesmo sem nenhum status,
        # entao so consideramos CI se houver status de fato (total_count > 0).
        combined = get(f"/repos/{repo}/commits/{sha}/status")
        if combined.get("total_count", 0) == 0:
            return "sem CI"
        st = combined.get("state", "")
        return {"success": "verde", "failure": "vermelho", "pending": "pendente"}.get(
            st, "sem CI"
        )
    conclusoes = [r.get("conclusion") for r in runs]
    if any(c in ("failure", "timed_out", "cancelled") for c in conclusoes):
        return "vermelho"
    if any(c is None for c in conclusoes):
        return "pendente"
    if all(c in ("success", "skipped", "neutral") for c in conclusoes):
        return "verde"
    return "pendente"


def status_review(repo: str, numero: int) -> str:
    """aprovado | mudancas | sem review"""
    reviews = get(f"/repos/{repo}/pulls/{numero}/reviews")
    ultimo: dict[str, str] = {}
    for r in reviews:
        autor = (r.get("user") or {}).get("login", "?")
        estado = r.get("state", "")
        if estado in ("APPROVED", "CHANGES_REQUESTED"):
            ultimo[autor] = estado
    if any(v == "CHANGES_REQUESTED" for v in ultimo.values()):
        return "mudancas"
    if any(v == "APPROVED" for v in ultimo.values()):
        return "aprovado"
    return "sem review"


def coletar_prs(repo: str) -> list[dict]:
    prs = get(f"/repos/{repo}/pulls?state=open&per_page=50")
    resultado = []
    for p in prs:
        numero = p["number"]
        detalhe = get(f"/repos/{repo}/pulls/{numero}")
        sha = detalhe["head"]["sha"]
        resultado.append(
            {
                "numero": numero,
                "titulo": p["title"],
                "draft": p.get("draft", False),
                "ci": status_ci(repo, sha),
                "review": status_review(repo, numero),
                "mergeable": detalhe.get("mergeable"),
                "mergeable_state": detalhe.get("mergeable_state", ""),
            }
        )
    return resultado


# --------------------------------------------------------------------------- #
def classificar(pr: dict) -> str:
    """pronto | bloqueado | andamento"""
    if pr["ci"] == "vermelho" or pr["review"] == "mudancas" or pr["mergeable"] is False:
        return "bloqueado"
    if (
        not pr["draft"]
        and pr["review"] == "aprovado"
        and pr["ci"] in ("verde", "sem CI")
        and pr["mergeable"] is True
    ):
        return "pronto"
    return "andamento"


def motivo_bloqueio(pr: dict) -> str:
    motivos = []
    if pr["ci"] == "vermelho":
        motivos.append("CI vermelho")
    if pr["review"] == "mudancas":
        motivos.append("mudancas solicitadas")
    if pr["mergeable"] is False:
        motivos.append("conflito de merge")
    return ", ".join(motivos) or "verificar"


def cmd_prs(args) -> int:
    repo = args.repo or detectar_repo()
    prs = coletar_prs(repo)
    print(f"== PRs abertos em {repo} ({len(prs)}) ==\n")
    header = f"{'PR':<5} {'CI':<9} {'Review':<10} {'Merge':<10} Titulo"
    print(header)
    print("-" * (len(header) + 20))
    for p in prs:
        draft = " (draft)" if p["draft"] else ""
        mrg = "sim" if p["mergeable"] else ("nao" if p["mergeable"] is False else "?")
        print(f"#{p['numero']:<4} {p['ci']:<9} {p['review']:<10} {mrg:<10} {p['titulo'][:45]}{draft}")
    return 0


def cmd_relatorio(args) -> int:
    repo = args.repo or detectar_repo()
    prs = coletar_prs(repo)
    grupos = {"pronto": [], "bloqueado": [], "andamento": []}
    for p in prs:
        grupos[classificar(p)].append(p)

    print(f"== Relatorio de engenharia — {repo} (modo economia) ==\n")
    print(f"PRs abertos: {len(prs)} | prontos: {len(grupos['pronto'])} | "
          f"bloqueados: {len(grupos['bloqueado'])} | em andamento: {len(grupos['andamento'])}\n")

    if grupos["pronto"]:
        print("PRONTOS PARA MERGE (precisa do OK do Joao):")
        for p in grupos["pronto"]:
            print(f"  - #{p['numero']} {p['titulo']}")
    if grupos["bloqueado"]:
        print("\nBLOQUEIOS:")
        for p in grupos["bloqueado"]:
            print(f"  - #{p['numero']} {p['titulo']} -> {motivo_bloqueio(p)}")
    if not grupos["pronto"] and not grupos["bloqueado"]:
        print("Nada exige acao agora (todos em andamento/draft).")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Toolkit de Engenharia (Codigo + GitHub)")
    parser.add_argument("--repo", help="owner/repo (senao detecta do git/env)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prs", help="lista PRs abertos com CI/review/merge")
    sub.add_parser("relatorio", help="modo economia: pronto p/ merge x bloqueios")

    args = parser.parse_args()
    try:
        return {"prs": cmd_prs, "relatorio": cmd_relatorio}[args.cmd](args)
    except requests.HTTPError as exc:
        print(f"[erro] GitHub API: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
