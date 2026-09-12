#!/usr/bin/env python3
"""Gerente geral (enxuto) do Joao Victor.

Coordena os bots Codigo, Conteudo, Carreira, Comercio e E-mails.

Principio de ECONOMIA DE CREDITO:
  - Sem fan-out: NUNCA roda todos os bots de uma vez.
  - Sem panorama automatico: nao gera relatorio geral sozinho.
  - So acorda o bot certo SOB DEMANDA e sobe apenas o resultado/bloqueio.

Uso:
  gerente bots                      -> lista os bots e o que fazem
  gerente <bot> <comando> [args...] -> acorda SO aquele bot e repassa o comando

Exemplos:
  gerente carreira placar
  gerente codigo relatorio
  gerente conteudo agenda --por-semana 3 --semanas 2
  gerente emails triagem --demo
  gerente comercio fornecedor --sku MAG-KIT-14
  gerente divulgacao rodar
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Registro dos bots: nome -> (script, descricao curta)
BOTS = {
    "codigo": ("codigo/codigo.py", "PRs, CI, reviews e status de merge"),
    "conteudo": ("conteudo/conteudo.py", "roteiros, fila e agenda de posts"),
    "carreira": ("carreira/carreira.py", "vagas remotas e placar de candidaturas"),
    "comercio": ("comercio/comercio.py", "catalogo, precificacao, fornecedor e relatorio"),
    "emails": ("emails/triagem.py", "triagem do Gmail e rascunhos"),
    "divulgacao": ("automation/github_to_linkedin.py", "GitHub -> LinkedIn (dry-run sem token)"),
    "web": ("common/web.py", "busca e acesso a internet (buscar / fetch)"),
}


def script_de(bot: str) -> Path:
    return REPO / BOTS[bot][0]


def listar_bots() -> int:
    print("== Gerente: bots disponiveis (acordo sob demanda) ==\n")
    for nome, (rel, desc) in BOTS.items():
        estado = "ok" if script_de(nome).exists() else "AUSENTE (merge o PR do bot)"
        print(f"  {nome:<9} [{estado}] — {desc}")
    print("\nUse: gerente <bot> <comando> [args...]  (aciona SO aquele bot)")
    print("Sem fan-out: o Gerente nunca roda todos de uma vez (economia de credito).")
    return 0


def acordar(bot: str, args: list[str]) -> int:
    script = script_de(bot)
    if not script.exists():
        print(
            f"[bloqueio] bot '{bot}' ausente neste repo ({BOTS[bot][0]}).\n"
            f"Faça o merge do PR desse bot para o Gerente conseguir acorda-lo.",
            file=sys.stderr,
        )
        return 2
    print(f"[gerente] acordando '{bot}' sob demanda...\n", flush=True)
    proc = subprocess.run([sys.executable, str(script), *args])
    if proc.returncode != 0:
        print(f"\n[gerente] '{bot}' retornou bloqueio (codigo {proc.returncode}).")
    return proc.returncode


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if argv[0] == "bots":
        return listar_bots()

    bot = argv[0]
    if bot not in BOTS:
        print(f"[erro] bot desconhecido: '{bot}'. Rode 'gerente bots' para ver a lista.")
        return 1
    if len(argv) < 2:
        print(f"[erro] diga o comando para o '{bot}'. Ex.: gerente {bot} <comando>")
        return 1
    return acordar(bot, argv[1:])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
