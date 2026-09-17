"""Faz uma consulta ao livro e mostra os k trechos mais relevantes.

Uso:
    python scripts/consultar.py --consulta "o que e recursao"
    python scripts/consultar.py --consulta "como funciona um dicionario" --k 5 --config C3

C1 e busca linear com Insertion Sort; C2 e indice invertido com busca binaria
e Merge Sort dos candidatos; C3 e busca linear com Merge Sort.
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
from paa_context.indice import buscar_indexado, construir_indice  # noqa: E402
from paa_context.modelos import carregar_chunks  # noqa: E402
from paa_context.insertion_sort import insertion_sort  # noqa: E402
from paa_context.linear_search import linear_search  # noqa: E402
from paa_context.merge_sort import merge_sort  # noqa: E402
from paa_context.pipeline import top_k  # noqa: E402
from paa_context.relevance import build_statistics  # noqa: E402

CHUNKS_PADRAO = RAIZ / "data" / "processed" / "chunks.jsonl"

ORDENADORES = {"C1": insertion_sort, "C3": merge_sort}


def consultar(chunks, estatisticas, consulta: str, k: int, config: str, indice=None):
    """Devolve (resultados, contador, candidatos) para a configuracao pedida.

    Na C2 o contador soma as comparacoes da busca binaria e do Merge Sort.
    """
    contador = Contador()

    if config == "C2":
        pontuados = buscar_indexado(consulta, indice, estatisticas, contador=contador)
        ordenados = merge_sort(pontuados, contador=contador)
    elif config in ORDENADORES:
        # A busca linear ja devolve so os candidatos (escore > 0), na ordem do livro.
        pontuados = linear_search(consulta, chunks, estatisticas)
        ordenados = ORDENADORES[config](pontuados, contador=contador)
    else:
        raise ValueError(f"configuracao {config} desconhecida; use C1, C2 ou C3")

    return top_k(ordenados, k), contador, len(pontuados)


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opcoes.add_argument("--consulta", required=True)
    opcoes.add_argument("--k", type=int, default=5)
    opcoes.add_argument("--config", default="C1", choices=["C1", "C2", "C3"])
    opcoes.add_argument("--chunks", type=Path, default=CHUNKS_PADRAO)
    opcoes.add_argument("--largura", type=int, default=120, help="letras do trecho exibidas")
    args = opcoes.parse_args()

    if not args.chunks.exists():
        print(f"nao encontrei {args.chunks}. Rode antes: python scripts/preparar_corpus.py", file=sys.stderr)
        return 1

    chunks = carregar_chunks(args.chunks)
    estatisticas = build_statistics(chunks)
    indice = construir_indice(chunks) if args.config == "C2" else None

    inicio = time.perf_counter_ns()
    resultados, contador, candidatos = consultar(chunks, estatisticas, args.consulta, args.k, args.config, indice)
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
    print(f"chunks no corpus: {len(chunks)}   candidatos com escore > 0: {candidatos}   "
          f"comparacoes: {contador.comparacoes}   trocas: {contador.trocas}   "
          f"tempo: {duracao_ms:.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
