#!/usr/bin/env python3
"""Toolkit do assistente de Comercio (dropshipping Kits MagSafe).

Faz as partes deterministicas e GRATUITAS do trabalho do bot Comercio:
  - precificar : calcula o preco de venda para bater a margem alvo (com taxas Shopee)
  - lucro      : dado um preco de venda, mostra lucro e margem
  - relatorio  : resumo "modo economia" (resultado + bloqueios)
  - brief      : gera o pedido de criativo para o time de Conteudo

Nao publica na Shopee/TikTok nem gasta dinheiro: isso continua manual, com o
"ok" explicito do Joao, exatamente como a regra do bot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG_PATH = BASE / "config.json"
CATALOGO_PATH = BASE / "catalogo.json"


def carregar_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def brl(valor: float) -> str:
    txt = f"{valor:,.2f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {txt}"


# --------------------------------------------------------------------------- #
# Matematica de precificacao
# --------------------------------------------------------------------------- #
def taxa_shopee(preco: float, shopee: dict) -> float:
    taxa = preco * shopee["comissao_pct"] + shopee["taxa_fixa_por_item"]
    return min(taxa, shopee.get("taxa_maxima", float("inf")))


def preco_para_margem(custo: float, margem_alvo: float, shopee: dict) -> float | None:
    """Preco de venda necessario para atingir a margem alvo (sobre a venda).

    lucro = preco*(1-com) - taxa_fixa - custo ; margem = lucro/preco
    => preco = (custo + taxa_fixa) / (1 - com - margem_alvo)
    Retorna None se a margem for inviavel (denominador <= 0).
    """
    com = shopee["comissao_pct"]
    fixa = shopee["taxa_fixa_por_item"]
    denom = 1 - com - margem_alvo
    if denom <= 0:
        return None
    return (custo + fixa) / denom


def resultado_para_preco(custo: float, preco: float, shopee: dict) -> dict:
    taxa = taxa_shopee(preco, shopee)
    lucro = preco - custo - taxa
    margem = (lucro / preco) if preco > 0 else 0.0
    return {"preco": preco, "taxa": taxa, "lucro": lucro, "margem": margem}


# --------------------------------------------------------------------------- #
# Helpers de catalogo
# --------------------------------------------------------------------------- #
def produtos_ativos(catalogo: dict) -> list[dict]:
    return [p for p in catalogo.get("produtos", []) if p.get("ativo", True)]


def margem_do_produto(produto: dict, config: dict) -> float:
    m = produto.get("margem_alvo")
    return m if m is not None else config["margem_alvo_padrao"]


def bloqueios_do_produto(produto: dict) -> list[str]:
    b = []
    if not produto.get("custo_fornecedor"):
        b.append("sem custo_fornecedor")
    if not produto.get("link_fornecedor"):
        b.append("sem link_fornecedor")
    return b


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #
def cmd_precificar(args, config, catalogo) -> int:
    shopee = config["shopee"]
    print("== Precificacao (para bater a margem alvo) ==\n")
    header = f"{'SKU':<12} {'Custo':>10} {'Margem':>7} {'Preco venda':>13} {'Taxa Shopee':>13} {'Lucro':>10}"
    print(header)
    print("-" * len(header))
    for p in produtos_ativos(catalogo):
        custo = float(p.get("custo_fornecedor") or 0)
        frete = float(config.get("frete_extra_padrao") or 0)
        custo_total = custo + frete
        margem = margem_do_produto(p, config)
        if custo <= 0:
            print(f"{p['sku']:<12} {brl(custo):>10} {margem*100:>6.0f}%   (informe o custo_fornecedor)")
            continue
        preco = preco_para_margem(custo_total, margem, shopee)
        if preco is None:
            print(f"{p['sku']:<12} {brl(custo):>10} {margem*100:>6.0f}%   (margem inviavel com as taxas atuais)")
            continue
        r = resultado_para_preco(custo_total, preco, shopee)
        print(
            f"{p['sku']:<12} {brl(custo):>10} {margem*100:>6.0f}% "
            f"{brl(preco):>13} {brl(r['taxa']):>13} {brl(r['lucro']):>10}"
        )
    return 0


def cmd_lucro(args, config, catalogo) -> int:
    shopee = config["shopee"]
    r = resultado_para_preco(args.custo, args.preco, shopee)
    print("== Lucro para um preco de venda ==")
    print(f"Custo fornecedor : {brl(args.custo)}")
    print(f"Preco de venda   : {brl(args.preco)}")
    print(f"Taxa Shopee      : {brl(r['taxa'])}")
    print(f"Lucro liquido    : {brl(r['lucro'])}")
    print(f"Margem           : {r['margem']*100:.1f}%")
    return 0


def cmd_relatorio(args, config, catalogo) -> int:
    shopee = config["shopee"]
    ativos = produtos_ativos(catalogo)
    prontos, bloqueados = [], []
    for p in ativos:
        b = bloqueios_do_produto(p)
        (bloqueados if b else prontos).append((p, b))

    print("== Relatorio Comercio (modo economia) ==\n")
    print(f"Produtos ativos : {len(ativos)}")
    print(f"Prontos p/ venda: {len(prontos)}")
    print(f"Bloqueados      : {len(bloqueados)}\n")

    if prontos:
        print("PRONTOS:")
        for p, _ in prontos:
            custo = float(p["custo_fornecedor"])
            preco = preco_para_margem(custo, margem_do_produto(p, config), shopee)
            preco_txt = brl(preco) if preco else "margem inviavel"
            print(f"  - {p['sku']} ({p['modelo']}): venda sugerida {preco_txt}")
    if bloqueados:
        print("\nBLOQUEIOS (precisa de acao):")
        for p, b in bloqueados:
            print(f"  - {p['sku']} ({p['modelo']}): {', '.join(b)}")
    print("\nAcoes que exigem OK do Joao: publicar produto, gastar com fornecedor/ads.")
    return 0


def cmd_brief(args, config, catalogo) -> int:
    alvo = {p["sku"].lower(): p for p in produtos_ativos(catalogo)}
    p = alvo.get(args.sku.lower())
    if not p:
        print(f"SKU '{args.sku}' nao encontrado no catalogo.")
        return 1
    print("== Brief de criativo (para o time de Conteudo) ==\n")
    print(f"Produto : {p['nome']} ({p['modelo']})")
    print(f"SKU     : {p['sku']}")
    print("Formato : 1 imagem principal (1:1) + 3 secundarias + 1 video curto (9:16)")
    print("Mensagem: destacar carregamento magnetico, compatibilidade e frete rapido")
    print("Tom     : direto, jovem, foco em beneficio")
    print("CTA     : 'Garanta o seu' / link da Shopee")
    print("Entrega : arquivos + legenda pronta em pt-BR")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Toolkit do assistente de Comercio")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("precificar", help="calcula preco de venda para a margem alvo")

    pl = sub.add_parser("lucro", help="lucro/margem dado um preco de venda")
    pl.add_argument("--custo", type=float, required=True, help="custo do fornecedor")
    pl.add_argument("--preco", type=float, required=True, help="preco de venda")

    sub.add_parser("relatorio", help="resumo modo economia (resultado + bloqueios)")

    pb = sub.add_parser("brief", help="gera brief de criativo para o Conteudo")
    pb.add_argument("sku", help="SKU do produto (ex.: MAG-KIT-14)")

    args = parser.parse_args()
    config = carregar_json(CONFIG_PATH)
    catalogo = carregar_json(CATALOGO_PATH)

    comandos = {
        "precificar": cmd_precificar,
        "lucro": cmd_lucro,
        "relatorio": cmd_relatorio,
        "brief": cmd_brief,
    }
    return comandos[args.cmd](args, config, catalogo)


if __name__ == "__main__":
    raise SystemExit(main())
