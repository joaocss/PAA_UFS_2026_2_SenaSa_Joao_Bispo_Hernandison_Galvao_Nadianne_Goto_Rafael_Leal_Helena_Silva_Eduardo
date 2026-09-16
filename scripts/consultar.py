"""Faz uma consulta ao livro e mostra os k trechos mais relevantes.

Uso:
    python scripts/consultar.py --consulta "o que e recursao"
    python scripts/consultar.py --consulta "como funciona um dicionario" --k 5 --config C3

C1 e busca linear com Insertion Sort; C3 e busca linear com Merge Sort.
C2 (indice invertido com busca binaria) entra na semana 2.
Precisa de data/processed/chunks.jsonl, gerado por scripts/preparar_corpus.py.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.contador import Contador  # noqa: E402
from paa_context.modelos import carregar_chunks  # noqa: E402
from paa_context.insertion_sort import insertion_sort  # noqa: E402
from paa_context.linear_search import linear_search  # noqa: E402
from paa_context.merge_sort import merge_sort  # noqa: E402
from paa_context.pipeline import top_k  # noqa: E402
from paa_context.relevance import build_statistics  # noqa: E402

CHUNKS_PADRAO = RAIZ / "data" / "processed" / "chunks.jsonl"

ORDENADORES = {"C1": insertion_sort, "C3": merge_sort}


def consultar(chunks, estatisticas, consulta: str, k: int, config: str):
    """Devolve (resultados, contador, candidatos) para a configuracao pedida."""
    if config not in ORDENADORES:
        raise ValueError(f"configuracao {config} indisponivel; use C1 ou C3")

    # A busca linear ja devolve so os candidatos (escore > 0), na ordem do livro.
    pontuados = linear_search(consulta, chunks, estatisticas)

    contador = Contador()
    ordenados = ORDENADORES[config](pontuados, contador=contador)
    return top_k(ordenados, k), contador, len(pontuados)


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opcoes.add_argument("--consulta", required=True)
    opcoes.add_argument("--k", type=int, default=5)
    opcoes.add_argument("--config", default="C1", choices=["C1", "C2", "C3"])
    opcoes.add_argument("--chunks", type=Path, default=CHUNKS_PADRAO)
    opcoes.add_argument("--largura", type=int, default=120, help="letras do trecho exibidas")
    args = opcoes.parse_args()

    if args.config == "C2":
        print("C2 (indice invertido + busca binaria) ainda nao esta integrado. Use C1 ou C3.")
        return 2
    if not args.chunks.exists():
        print(f"nao encontrei {args.chunks}. Rode antes: python scripts/preparar_corpus.py", file=sys.stderr)
        return 1

    chunks = carregar_chunks(args.chunks)
    estatisticas = build_statistics(chunks)

    inicio = time.perf_counter_ns()
    resultados, contador, candidatos = consultar(chunks, estatisticas, args.consulta, args.k, args.config)
    duracao_ms = (time.perf_counter_ns() - inicio) / 1e6

    print(f'consulta: "{args.consulta}"  config: {args.config}  k: {args.k}')
    print()
    if not resultados:
        print("nenhum trecho contem termos da consulta.")
    for posicao, (chunk, escore) in enumerate(resultados, start=1):
        onde = chunk.capitulo + (f" > {chunk.secao}" if chunk.secao else "")
        print(f"{posicao}. {chunk.chunk_id}  [{chunk.tipo}]  escore {escore:.4f}")
        print(f"   {onde}")
        print(f"   {chunk.texto[:args.largura]}...")
    print()
    print(f"chunks varridos: {len(chunks)}   candidatos com escore > 0: {candidatos}   "
          f"comparacoes: {contador.comparacoes}   trocas: {contador.trocas}   "
          f"tempo: {duracao_ms:.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
