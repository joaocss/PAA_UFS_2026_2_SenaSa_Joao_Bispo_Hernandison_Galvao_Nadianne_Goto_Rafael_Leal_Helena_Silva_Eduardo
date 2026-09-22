"""Roda o experimento principal e grava uma linha por execucao (contrato 04).

Uso:
    python scripts/rodar_experimentos.py
    python scripts/rodar_experimentos.py --rapido     # 3 consultas, 1 repeticao: so para conferir que roda

Desenho (docs/PROTOCOLO_EXPERIMENTAL.md): configuracoes C1, C2, C3 e C4
(referencia) x tamanhos 25, 50 e 100 % dos chunks, sorteados por capitulo com
semente fixa x as 30 consultas de data/queries.csv x k em 5 e 10 x 5
repeticoes, depois de 2 aquecimentos descartados. A ordem das configuracoes e
sorteada em cada bloco.

Cada execucao e medida de ponta a ponta, com os tempos separados:
  tempo_ingestao_ns    estatisticas do corpus (N e df), refeitas a cada execucao
  tempo_indice_ns      construcao do indice invertido (C2) ou do TfidfVectorizer (C4); 0 em C1 e C3
  tempo_busca_ns       pontuacao dos candidatos (varredura em C1 e C3, indice em C2)
  tempo_ordenacao_ns   Insertion Sort (C1) ou Merge Sort (C2, C3); em C4 a biblioteca faz tudo junto, e fica em tempo_busca_ns
  tempo_consulta_ns    busca + ordenacao + corte top-k
  tempo_total_ns       ingestao + indice + consulta
O campo tempo_ordenacao_ou_indice_ns do contrato 04 e o indice em C2 e C4 e a ordenacao em C1 e C3.

A memoria de pico vem de uma execucao extra com tracemalloc, fora do
cronometro, porque o tracemalloc deixa o Python varias vezes mais lento.

Saidas: experimentos/brutos/execucoes.jsonl e experimentos/logs/ambiente.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import socket
import subprocess
import sys
import time
import tracemalloc
from collections import defaultdict
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.contador import Contador  # noqa: E402
from paa_context.indice import buscar_indexado, construir_indice  # noqa: E402
from paa_context.insertion_sort import insertion_sort  # noqa: E402
from paa_context.linear_search import linear_search  # noqa: E402
from paa_context.merge_sort import merge_sort  # noqa: E402
from paa_context.modelos import carregar_chunks  # noqa: E402
from paa_context.pipeline import top_k  # noqa: E402
from paa_context.referencia import construir_referencia, recuperar_referencia  # noqa: E402
from paa_context.relevance import build_statistics  # noqa: E402

CHUNKS = RAIZ / "data" / "processed" / "chunks.jsonl"
CONSULTAS = RAIZ / "data" / "queries.csv"
BRUTOS = RAIZ / "experimentos" / "brutos" / "execucoes.jsonl"
AMBIENTE = RAIZ / "experimentos" / "logs" / "ambiente.json"

CONFIGS = ["C1", "C2", "C3", "C4"]
TAMANHOS = [25, 50, 100]
VALORES_K = [5, 10]
REPETICOES = 5
AQUECIMENTOS = 2
SEMENTE = 2026
CHUNK_SIZE = 256
OVERLAP = 32


def amostrar_por_capitulo(chunks, percentual, semente):
    """Sorteia `percentual` % dos chunks de cada notebook, e devolve na ordem do livro."""
    if percentual == 100:
        return list(chunks)
    sorteio = random.Random(f"{semente}-{percentual}")
    por_arquivo = defaultdict(list)
    for chunk in chunks:
        por_arquivo[chunk.arquivo].append(chunk)
    escolhidos = []
    for arquivo in sorted(por_arquivo):
        grupo = por_arquivo[arquivo]
        quantidade = max(1, round(len(grupo) * percentual / 100))
        escolhidos.extend(sorteio.sample(grupo, quantidade))
    return sorted(escolhidos, key=lambda chunk: chunk.source_order)


def executar(config, chunks, consulta, k):
    """Uma execucao completa. Devolve (resultados, contador ou None, candidatos, tempos em ns)."""
    t0 = time.perf_counter_ns()
    estatisticas = build_statistics(chunks)
    t1 = time.perf_counter_ns()

    contador = Contador()
    if config == "C2":
        indice = construir_indice(chunks)
        t2 = time.perf_counter_ns()
        pontuados = buscar_indexado(consulta, indice, estatisticas, contador=contador)
        t3 = time.perf_counter_ns()
        ordenados = merge_sort(pontuados, contador=contador)
        t4 = time.perf_counter_ns()
        resultados = top_k(ordenados, k)
        candidatos = len(pontuados)
    elif config == "C4":
        referencia = construir_referencia(chunks)
        t2 = time.perf_counter_ns()
        resultados, candidatos = recuperar_referencia(consulta, referencia, k)
        t3 = t4 = time.perf_counter_ns()
        contador = None
    else:
        t2 = t1
        pontuados = linear_search(consulta, chunks, estatisticas)
        t3 = time.perf_counter_ns()
        ordenar = insertion_sort if config == "C1" else merge_sort
        ordenados = ordenar(pontuados, contador=contador)
        t4 = time.perf_counter_ns()
        resultados = top_k(ordenados, k)
        candidatos = len(pontuados)
    t5 = time.perf_counter_ns()

    tempos = {
        "tempo_ingestao_ns": t1 - t0,
        "tempo_indice_ns": t2 - t1,
        "tempo_busca_ns": t3 - t2,
        "tempo_ordenacao_ns": t4 - t3,
        "tempo_consulta_ns": t5 - t2,
        "tempo_total_ns": t5 - t0,
    }
    return resultados, contador, candidatos, tempos


def memoria_pico(config, chunks, consulta, k):
    tracemalloc.start()
    executar(config, chunks, consulta, k)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico


def commit_atual():
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()
        sujo = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
        return commit + ("-modificado" if sujo else "")
    except (OSError, subprocess.CalledProcessError):
        return "desconhecido"


def sysctl(chave):
    try:
        return subprocess.run(["sysctl", "-n", chave], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def versao(pacote):
    try:
        return metadata.version(pacote)
    except metadata.PackageNotFoundError:
        return None


def registrar_ambiente(commit, argumentos, inicio, fim, divergencias, n_execucoes):
    memoria = sysctl("hw.memsize")
    ambiente = {
        "inicio": inicio,
        "fim": fim,
        "commit": commit,
        "comando": " ".join([Path(sys.executable).name] + sys.argv),
        "argumentos": argumentos,
        "host": socket.gethostname(),
        "sistema": platform.platform(),
        "processador": sysctl("machdep.cpu.brand_string") or platform.processor(),
        "nucleos": os.cpu_count(),
        "memoria_bytes": int(memoria) if memoria else None,
        "python": platform.python_version(),
        "bibliotecas": {p: versao(p) for p in ["scikit-learn", "numpy", "scipy", "matplotlib"]},
        "semente": SEMENTE,
        "n_execucoes": n_execucoes,
        "divergencias_c1_c2_c3": divergencias,
    }
    AMBIENTE.parent.mkdir(parents=True, exist_ok=True)
    AMBIENTE.write_text(json.dumps(ambiente, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opcoes.add_argument("--rapido", action="store_true", help="3 consultas, 1 repeticao, sem aquecimento")
    args = opcoes.parse_args()

    if not CHUNKS.exists():
        print(f"nao encontrei {CHUNKS}. Rode antes: python scripts/preparar_corpus.py", file=sys.stderr)
        return 1

    todos = carregar_chunks(CHUNKS)
    consultas = list(csv.DictReader(CONSULTAS.open(encoding="utf-8")))
    repeticoes, aquecimentos = REPETICOES, AQUECIMENTOS
    if args.rapido:
        consultas, repeticoes, aquecimentos = consultas[:3], 1, 0

    commit = commit_atual()
    inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sorteio_ordem = random.Random(SEMENTE)
    divergencias = []
    n_execucoes = 0
    BRUTOS.parent.mkdir(parents=True, exist_ok=True)

    with BRUTOS.open("w", encoding="utf-8") as saida:
        for tamanho in TAMANHOS:
            chunks = amostrar_por_capitulo(todos, tamanho, SEMENTE)
            print(f"tamanho {tamanho} %: {len(chunks)} chunks", flush=True)
            for consulta in consultas:
                for k in VALORES_K:
                    memoria = {config: memoria_pico(config, chunks, consulta["texto"], k) for config in CONFIGS}
                    listas = {}
                    for repeticao in range(-aquecimentos, repeticoes):
                        ordem = CONFIGS[:]
                        sorteio_ordem.shuffle(ordem)
                        for config in ordem:
                            resultados, contador, candidatos, tempos = executar(config, chunks, consulta["texto"], k)
                            if repeticao < 0:
                                continue
                            ids = [chunk.chunk_id for chunk, _ in resultados]
                            listas[config] = ids
                            n_execucoes += 1
                            linha = {
                                "run_id": f"t{tamanho}-{consulta['query_id']}-k{k}-{config}-r{repeticao + 1}",
                                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "commit": commit,
                                "host": socket.gethostname(),
                                "python_versao": platform.python_version(),
                                "config": config,
                                "query_id": consulta["query_id"],
                                "categoria": consulta["categoria"],
                                "k": k,
                                "chunk_size": CHUNK_SIZE,
                                "overlap": OVERLAP,
                                "tamanho_corpus": tamanho,
                                "semente": SEMENTE,
                                "repeticao": repeticao + 1,
                                "tempo_ingestao_ns": tempos["tempo_ingestao_ns"],
                                "tempo_ordenacao_ou_indice_ns": tempos["tempo_indice_ns"] if config in ("C2", "C4") else tempos["tempo_ordenacao_ns"],
                                "tempo_consulta_ns": tempos["tempo_consulta_ns"],
                                "tempo_total_ns": tempos["tempo_total_ns"],
                                "tempo_indice_ns": tempos["tempo_indice_ns"],
                                "tempo_busca_ns": tempos["tempo_busca_ns"],
                                "tempo_ordenacao_ns": tempos["tempo_ordenacao_ns"],
                                "memoria_pico_bytes": memoria[config],
                                "comparacoes": contador.comparacoes if contador else None,
                                "trocas": contador.trocas if contador else None,
                                "n_chunks": len(chunks),
                                "n_candidatos": candidatos,
                                "n_resultados": len(resultados),
                                "resultado_vazio": not resultados,
                                "resultado_ids": ids,
                            }
                            saida.write(json.dumps(linha, ensure_ascii=False) + "\n")
                    if not (listas["C1"] == listas["C2"] == listas["C3"]):
                        divergencias.append(f"t{tamanho}-{consulta['query_id']}-k{k}")
            saida.flush()

    fim = datetime.now(timezone.utc).isoformat(timespec="seconds")
    registrar_ambiente(commit, vars(args), inicio, fim, divergencias, n_execucoes)
    print(f"{n_execucoes} execucoes em {BRUTOS.relative_to(RAIZ)}; divergencias entre C1, C2 e C3: {len(divergencias)}")
    return 0 if not divergencias else 2


if __name__ == "__main__":
    raise SystemExit(principal())
