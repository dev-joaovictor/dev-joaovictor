#!/usr/bin/env python3
"""Toolkit do assistente de Conteudo do Joao Victor (TikTok @joaovictor1639).

Faz as partes gratuitas e deterministicas do bot Conteudo:
  - roteiro : gera um roteiro de 30-60s (gancho / corpo / CTA) para um tema
  - criativo: gera roteiro + legenda de um produto (quando o Comercio pede)
  - fila    : lista a fila de videos
  - add     : adiciona um tema na fila
  - status  : muda o status de um item da fila
  - agenda  : monta um calendario de 2-3 posts/semana ESPACADOS (nunca em lote)

Nao publica no TikTok: automatizar o app viola os termos. Publicar continua
manual, com o "ok" explicito do Joao (regra do proprio bot).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
FILA_PATH = BASE / "fila.json"

STATUS_VALIDOS = ["ideia", "roteiro", "gravado", "aprovado", "postado"]

# Dias da semana por frequencia (0=segunda ... 6=domingo) e horarios espacados
DIAS_POR_FREQ = {2: [1, 3], 3: [0, 2, 4]}
HORARIOS = ["11:00", "19:00", "15:00"]


def carregar_fila() -> dict:
    return json.loads(FILA_PATH.read_text(encoding="utf-8"))


def salvar_fila(fila: dict) -> None:
    FILA_PATH.write_text(json.dumps(fila, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Geracao de roteiro / criativo
# --------------------------------------------------------------------------- #
def montar_roteiro(tema: str, conta: str, cta: str | None = None) -> str:
    cta = cta or f"Segue a {conta} pra mais dicas!"
    linhas = [
        f"ROTEIRO 30-60s — {tema}",
        "",
        "[0-3s] GANCHO: comece com uma pergunta forte ou promessa sobre "
        f"'{tema}'.",
        "[3-12s] CONTEXTO: por que isso importa pra quem assiste.",
        "[12-40s] DESENVOLVIMENTO: 3 pontos rapidos, um por vez, direto ao ponto.",
        "[40-52s] PROVA: mostre um exemplo real / na pratica.",
        f"[52-60s] CTA: {cta}",
        "",
        f"LEGENDA: {tema} — o que voce faria diferente? Comenta ai.",
        "HASHTAGS: #tech #dev #dicas #foryou #fyp",
    ]
    return "\n".join(linhas)


def montar_criativo_produto(nome: str, modelo: str) -> str:
    linhas = [
        f"CRIATIVO SHOPEE — {nome} ({modelo})",
        "",
        "[0-3s] GANCHO: 'Seu {modelo} merece isso' (mostra o produto na mao).".format(
            modelo=modelo
        ),
        "[3-15s] BENEFICIOS: carregamento magnetico, encaixe perfeito, praticidade.",
        "[15-30s] DEMONSTRACAO: colocar/tirar rapido, dia a dia.",
        "[30-40s] PROVA: 'chega rapido e com garantia'.",
        "[40-50s] CTA: 'Link na Shopee — garante o seu'.",
        "",
        f"LEGENDA: {nome} pro seu {modelo}. Praticidade que voce sente no primeiro uso.",
        "HASHTAGS: #magsafe #iphone #acessorios #shopee #achadinhos",
    ]
    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# Comandos de fila
# --------------------------------------------------------------------------- #
def cmd_roteiro(args) -> int:
    fila = carregar_fila()
    print(montar_roteiro(args.tema, fila.get("conta_tiktok", "@sua_conta")))
    return 0


def cmd_criativo(args) -> int:
    print(montar_criativo_produto(args.nome, args.modelo))
    return 0


def cmd_fila(args) -> int:
    fila = carregar_fila()
    videos = fila.get("videos", [])
    print(f"== Fila de videos ({fila.get('conta_tiktok','')}) — {len(videos)} item(ns) ==\n")
    for v in videos:
        print(f"  #{v['id']:<3} [{v['status']:<8}] {v['tema']}")
    return 0


def cmd_add(args) -> int:
    fila = carregar_fila()
    videos = fila.setdefault("videos", [])
    novo_id = max([v["id"] for v in videos], default=0) + 1
    videos.append({"id": novo_id, "tema": args.tema, "status": "ideia"})
    salvar_fila(fila)
    print(f"[ok] adicionado #{novo_id}: {args.tema}")
    return 0


def cmd_status(args) -> int:
    if args.novo not in STATUS_VALIDOS:
        print(f"status invalido. Use um de: {', '.join(STATUS_VALIDOS)}")
        return 1
    fila = carregar_fila()
    for v in fila.get("videos", []):
        if v["id"] == args.id:
            v["status"] = args.novo
            salvar_fila(fila)
            print(f"[ok] #{args.id} -> {args.novo}")
            return 0
    print(f"id #{args.id} nao encontrado.")
    return 1


def gerar_agenda(inicio: datetime, posts_por_semana: int, semanas: int, itens: list[dict]) -> list[dict]:
    dias = DIAS_POR_FREQ[posts_por_semana]
    total_desejado = posts_por_semana * semanas
    slots: list[datetime] = []
    semana = 0
    # Gera semanas ate juntar posts futuros suficientes (ignora horarios ja passados).
    while len(slots) < total_desejado and semana < semanas + 4:
        base = inicio + timedelta(weeks=semana)
        segunda = base - timedelta(days=base.weekday())  # segunda daquela semana
        for i, dia in enumerate(dias):
            hora, minuto = map(int, HORARIOS[i % len(HORARIOS)].split(":"))
            data = segunda + timedelta(days=dia)
            slot = data.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            if slot >= inicio:
                slots.append(slot)
        semana += 1
    slots = sorted(slots)[:total_desejado]

    agenda = []
    for i, slot in enumerate(slots):
        item = itens[i] if i < len(itens) else None
        agenda.append({"quando": slot, "tema": item["tema"] if item else "(fila vazia — adicione ideias)"})
    return agenda


def cmd_agenda(args) -> int:
    if args.por_semana not in DIAS_POR_FREQ:
        print("posts por semana deve ser 2 ou 3.")
        return 1
    fila = carregar_fila()
    pendentes = [v for v in fila.get("videos", []) if v["status"] != "postado"]
    inicio = datetime.now().replace(second=0, microsecond=0)
    agenda = gerar_agenda(inicio, args.por_semana, args.semanas, pendentes)

    dias_pt = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    print(f"== Agenda de posts ({args.por_semana}x/semana, espacados) ==\n")
    for a in agenda:
        d = a["quando"]
        print(f"  {dias_pt[d.weekday()]} {d.strftime('%d/%m %H:%M')} — {a['tema']}")
    print("\nRegra: nunca postar em lote. Publicar so com o OK do Joao.")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Toolkit do assistente de Conteudo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("roteiro", help="gera roteiro de 30-60s para um tema")
    pr.add_argument("tema")

    pc = sub.add_parser("criativo", help="gera criativo de produto (Shopee)")
    pc.add_argument("nome")
    pc.add_argument("modelo")

    sub.add_parser("fila", help="lista a fila de videos")

    pa = sub.add_parser("add", help="adiciona tema na fila")
    pa.add_argument("tema")

    ps = sub.add_parser("status", help="muda o status de um item")
    ps.add_argument("id", type=int)
    ps.add_argument("novo", help=f"um de: {', '.join(STATUS_VALIDOS)}")

    pg = sub.add_parser("agenda", help="monta calendario de posts")
    pg.add_argument("--por-semana", type=int, default=3, choices=[2, 3])
    pg.add_argument("--semanas", type=int, default=2)

    args = parser.parse_args()
    comandos = {
        "roteiro": cmd_roteiro,
        "criativo": cmd_criativo,
        "fila": cmd_fila,
        "add": cmd_add,
        "status": cmd_status,
        "agenda": cmd_agenda,
    }
    return comandos[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
