#!/usr/bin/env python3
"""Utilitario compartilhado de internet para os bots.

Da a cada bot a capacidade de "mexer na internet": fazer buscas e acessar
paginas. Usa a biblioteca padrao + requests, sem chaves de API.

  buscar(consulta)  -> lista de resultados {titulo, url, resumo}
  fetch(url)        -> texto (HTML) da pagina
  texto_limpo(html) -> HTML sem tags, util para leitura rapida

Uso via linha de comando:
  python common/web.py buscar "vagas python remoto"
  python common/web.py fetch https://example.com
"""
from __future__ import annotations

import html as _html
import re
import sys

import requests

DDG_HTML = "https://html.duckduckgo.com/html/"
UA = "Mozilla/5.0 (compatible; empresa-agentes/1.0)"
TIMEOUT = 25


def fetch(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def texto_limpo(html_str: str, limite: int = 2000) -> str:
    sem_script = re.sub(r"(?is)<(script|style).*?</\1>", " ", html_str)
    sem_tags = re.sub(r"(?s)<[^>]+>", " ", sem_script)
    texto = _html.unescape(re.sub(r"\s+", " ", sem_tags)).strip()
    return texto[:limite]


def buscar(consulta: str, limite: int = 8) -> list[dict]:
    resp = requests.post(
        DDG_HTML,
        data={"q": consulta},
        headers={"User-Agent": UA},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    resultados = []
    # Links de resultado no HTML do DuckDuckGo
    padrao = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S
    )
    resumo_pat = re.compile(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.S)
    resumos = [texto_limpo(s, 300) for s in resumo_pat.findall(resp.text)]
    for i, (url, titulo) in enumerate(padrao.findall(resp.text)[:limite]):
        resultados.append(
            {
                "titulo": texto_limpo(titulo, 200),
                "url": _html.unescape(url),
                "resumo": resumos[i] if i < len(resumos) else "",
            }
        )
    return resultados


def _cli(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    comando, arg = argv[0], " ".join(argv[1:])
    if comando == "buscar":
        for i, r in enumerate(buscar(arg), 1):
            print(f"{i}. {r['titulo']}\n   {r['url']}")
            if r["resumo"]:
                print(f"   {r['resumo']}")
        return 0
    if comando == "fetch":
        print(texto_limpo(fetch(arg), 3000))
        return 0
    print(f"comando desconhecido: {comando}")
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
