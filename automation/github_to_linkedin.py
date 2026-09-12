#!/usr/bin/env python3
"""Rotina: verifica o GitHub, elabora um texto de divulgacao de projetos e publica no LinkedIn.

Fluxo:
  1. Busca os repositorios do usuario na API publica do GitHub.
  2. Seleciona projetos relevantes (ignora forks e repos ja divulgados).
  3. Elabora um post profissional em portugues para cada projeto.
  4. Publica no LinkedIn pela API OFICIAL (escopo w_member_social).

Nada aqui automatiza login de navegador nem quebra de CAPTCHA: usa somente
APIs oficiais e um token que voce mesmo gera. Sem credenciais do LinkedIn o
script roda em modo "dry-run" (apenas mostra o texto que seria publicado).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

GITHUB_API = "https://api.github.com"
LINKEDIN_POSTS_API = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_USERINFO_API = "https://api.linkedin.com/v2/userinfo"
REQUEST_TIMEOUT = 20


# --------------------------------------------------------------------------- #
# Configuracao (via variaveis de ambiente / GitHub Secrets)
# --------------------------------------------------------------------------- #
def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on", "sim"}


class Config:
    def __init__(self) -> None:
        self.github_user = os.getenv("GITHUB_USERNAME", "dev-joaovictor").strip()
        self.github_token = os.getenv("GH_API_TOKEN", "").strip()
        self.linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
        self.linkedin_author = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
        self.max_posts = int(os.getenv("MAX_POSTS", "1"))
        self.include_forks = _env_bool("INCLUDE_FORKS", False)
        self.min_stars = int(os.getenv("MIN_STARS", "0"))
        self.skip_repos = {
            r.strip().lower()
            for r in os.getenv("SKIP_REPOS", "").split(",")
            if r.strip()
        }
        self.state_file = Path(
            os.getenv("STATE_FILE", "automation/state/posted.json")
        )
        # Sem token do LinkedIn nao ha como publicar => forca dry-run.
        self.dry_run = _env_bool("DRY_RUN", not bool(self.linkedin_token))


# --------------------------------------------------------------------------- #
# Estado (repos ja divulgados)
# --------------------------------------------------------------------------- #
def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"[aviso] estado invalido em {path}, recomecando.", file=sys.stderr)
    return {"posted": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# GitHub
# --------------------------------------------------------------------------- #
def fetch_repos(cfg: Config) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if cfg.github_token:
        headers["Authorization"] = f"Bearer {cfg.github_token}"
    url = f"{GITHUB_API}/users/{cfg.github_user}/repos"
    params = {"per_page": 100, "sort": "updated", "type": "owner"}
    resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def select_projects(repos: list[dict], cfg: Config, state: dict) -> list[dict]:
    already = set(state.get("posted", {}).keys())
    selected = []
    for repo in repos:
        name = repo.get("name", "")
        if repo.get("private"):
            continue
        if repo.get("fork") and not cfg.include_forks:
            continue
        if repo.get("archived"):
            continue
        if name.lower() in cfg.skip_repos:
            continue
        if name.lower() == cfg.github_user.lower():  # repo do proprio perfil
            continue
        if repo.get("stargazers_count", 0) < cfg.min_stars:
            continue
        if repo.get("full_name") in already:
            continue
        selected.append(repo)
    return selected


# --------------------------------------------------------------------------- #
# Elaboracao do post
# --------------------------------------------------------------------------- #
def _hashtags(repo: dict) -> str:
    tags = ["#desenvolvimento", "#programacao", "#opensource"]
    lang = (repo.get("language") or "").lower()
    lang_map = {
        "typescript": "#typescript",
        "javascript": "#javascript",
        "python": "#python",
        "html": "#webdev",
        "css": "#frontend",
        "java": "#java",
        "go": "#golang",
    }
    if lang in lang_map:
        tags.insert(0, lang_map[lang])
    for topic in repo.get("topics", [])[:3]:
        clean = "".join(ch for ch in topic if ch.isalnum())
        if clean:
            tags.append(f"#{clean}")
    # remove duplicatas preservando ordem
    seen, out = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " ".join(out)


def build_post(repo: dict) -> str:
    name = repo.get("name", "projeto")
    desc = (repo.get("description") or "").strip()
    lang = repo.get("language")
    url = repo.get("html_url", "")

    linha_desc = desc if desc else "Um novo projeto que venho desenvolvendo."

    linhas = [f"Novidade no meu GitHub: {name}", "", linha_desc]
    if lang:
        linhas += ["", f"Stack principal: {lang}."]
    linhas += [
        "",
        "Estou compartilhando esse projeto como parte da minha evolucao "
        "como desenvolvedor. Feedbacks e conexoes sao muito bem-vindos!",
        "",
        f"Codigo e detalhes: {url}",
        "",
        _hashtags(repo),
    ]
    return "\n".join(linhas).strip()


# --------------------------------------------------------------------------- #
# LinkedIn (API oficial)
# --------------------------------------------------------------------------- #
def resolve_author_urn(cfg: Config) -> str:
    if cfg.linkedin_author:
        return cfg.linkedin_author
    headers = {"Authorization": f"Bearer {cfg.linkedin_token}"}
    resp = requests.get(LINKEDIN_USERINFO_API, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    sub = resp.json().get("sub")
    if not sub:
        raise RuntimeError(
            "Nao consegui descobrir o URN do autor. Defina LINKEDIN_AUTHOR_URN."
        )
    return f"urn:li:person:{sub}"


def publish_to_linkedin(cfg: Config, author_urn: str, text: str) -> str:
    headers = {
        "Authorization": f"Bearer {cfg.linkedin_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    resp = requests.post(
        LINKEDIN_POSTS_API, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
    )
    resp.raise_for_status()
    return resp.headers.get("x-restli-id", resp.json().get("id", "publicado"))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    cfg = Config()
    print(f"== Rotina GitHub -> LinkedIn ==")
    print(f"Usuario GitHub: {cfg.github_user}")
    print(f"Modo: {'DRY-RUN (nao publica)' if cfg.dry_run else 'PUBLICACAO REAL'}")

    state = load_state(cfg.state_file)

    try:
        repos = fetch_repos(cfg)
    except requests.HTTPError as exc:
        print(f"[erro] falha ao consultar o GitHub: {exc}", file=sys.stderr)
        return 1

    projetos = select_projects(repos, cfg, state)
    print(f"Projetos elegiveis (ainda nao divulgados): {len(projetos)}")

    if not projetos:
        print("Nada novo para publicar. Ate a proxima rodada!")
        return 0

    author_urn = ""
    if not cfg.dry_run:
        author_urn = resolve_author_urn(cfg)
        print(f"Autor LinkedIn: {author_urn}")

    publicados = 0
    for repo in projetos[: cfg.max_posts]:
        texto = build_post(repo)
        print("\n" + "-" * 60)
        print(f"Projeto: {repo['full_name']}")
        print("-" * 60)
        print(texto)

        if cfg.dry_run:
            print("\n[dry-run] post NAO publicado (defina LINKEDIN_ACCESS_TOKEN).")
        else:
            post_id = publish_to_linkedin(cfg, author_urn, texto)
            print(f"\n[ok] publicado no LinkedIn (id: {post_id}).")
            state.setdefault("posted", {})[repo["full_name"]] = {
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "post_id": post_id,
            }
            publicados += 1

    if publicados:
        save_state(cfg.state_file, state)
        print(f"\nEstado atualizado: {cfg.state_file}")

    print(f"\nConcluido. Publicados nesta rodada: {publicados}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
