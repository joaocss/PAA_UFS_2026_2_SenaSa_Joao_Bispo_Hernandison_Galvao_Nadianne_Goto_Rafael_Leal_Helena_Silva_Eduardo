#!/usr/bin/env python3
"""Complementa o Contrato 08 sem alterar os 6.750 registros originais.

Uso (raiz do projeto):
  python scripts/av2/completar_contrato08.py --rapido
  python scripts/av2/completar_contrato08.py
  python scripts/av2/completar_contrato08.py --somente-metricas

Principal: S3 versus S5, 30 consultas x 3 n x 3 W x 3 repeticoes.
C3 inclui busca linear, Merge Sort e top-n; tempo do fluxo de consulta
inclui C3 + conversao + selecao. Ingestao/estatisticas medidas a parte.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from paa_context.modelos import carregar_chunks  # noqa: E402
from paa_context.pipeline import retrieve  # noqa: E402
from paa_context.relevance import build_statistics  # noqa: E402
from paa_context.selecao import (  # noqa: E402
    ESTRATEGIAS, itens_de_resultados,
)

BASE = RAIZ / "experimentos" / "av2"
BRUTOS = BASE / "brutos" / "execucoes.jsonl"
CONSULTAS = RAIZ / "data" / "queries.csv"
CORPUS_VERSIONADO = RAIZ / "data" / "chunks.jsonl"
CORPUS_PROCESSADO = RAIZ / "data" / "processed" / "chunks.jsonl"
NOMES_PRINCIPAIS = ("guloso_densidade", "mochila_dp")
SEMENTE = 2026
LIMIAR_JACCARD = 0.8


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arq:
        for bloco in iter(lambda: arq.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def corpus_efetivo() -> Path:
    if CORPUS_VERSIONADO.exists():
        return CORPUS_VERSIONADO
    if CORPUS_PROCESSADO.exists():
        return CORPUS_PROCESSADO
    raise FileNotFoundError("Nenhum corpus encontrado em data/chunks.jsonl ou data/processed/chunks.jsonl")


def hash_corpus() -> dict:
    saida = {}
    for nome, arq in (("versionado", CORPUS_VERSIONADO), ("processado", CORPUS_PROCESSADO)):
        saida[f"sha256_{nome}"] = sha256(arq) if arq.exists() else None
    a, b = saida.values()
    saida["equivalencia_corpus"] = (a == b) if (a is not None and b is not None) else None
    return saida


def ler_jsonl(arq: Path) -> list[dict]:
    with arq.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def ler_consultas() -> dict[str, str]:
    with CONSULTAS.open(encoding="utf-8-sig", newline="") as f:
        registros = list(csv.DictReader(f))
    consultas = {r["query_id"]: r["texto"] for r in registros}
    if len(consultas) != len(registros):
        raise ValueError("query_id repetido no arquivo de consultas")
    return consultas


def tokens(texto: str) -> set[str]:
    return set(texto.casefold().split())


def redundancia(ids: list[str], indice_textos: dict[str, str], limiar=LIMIAR_JACCARD) -> dict:
    """Pares redundantes por Jaccard dos conjuntos de palavras dos chunks."""
    if len(ids) != len(set(ids)):
        raise ValueError("IDs duplicados na selecao")
    conjuntos = []
    for cid in ids:
        if cid not in indice_textos:
            raise KeyError(f"chunk ausente do corpus: {cid}")
        conjuntos.append(tokens(indice_textos[cid]))
    pares = 0
    redundantes = 0
    for a, b in combinations(conjuntos, 2):
        pares += 1
        uniao = a | b
        similaridade = len(a & b) / len(uniao) if uniao else 1.0
        if similaridade >= limiar:
            redundantes += 1
    return {
        "pares_possiveis": pares,
        "pares_redundantes": redundantes,
        "taxa_pares_redundantes": redundantes / pares if pares else None,
    }


def calcular_metricas_complementares(registros: list[dict], indice_textos: dict[str, str]) -> list[dict]:
    """Uma linha por consulta,n,W,estrategia; sem duplicar 5 repeticoes."""
    grupos = defaultdict(list)
    for r in registros:
        chave = (r["query_id"], int(r["n_solicitado"]), int(r["W"]), r["estrategia"])
        grupos[chave].append(r)
    otimos = {}
    for chave, grupo in grupos.items():
        if chave[3] == "mochila_dp":
            valores = {r["valor_quantizado"] for r in grupo}
            if len(valores) != 1:
                raise ValueError(f"Valor da DP varia entre repeticoes: {chave}")
            otimos[chave[:3]] = valores.pop()
    if len(otimos) != len({k[:3] for k in grupos}):
        raise ValueError("Cenarios sem referencia da DP")
    saida = []
    for chave, grupo in sorted(grupos.items()):
        qid, n, W, estrategia = chave
        valores = {(r["valor_quantizado"], tuple(r["ids_selecionados"]), r["custo_total"]) for r in grupo}
        if len(valores) != 1:
            raise ValueError(f"Selecao nao deterministica: {chave}")
        valor, ids, custo = next(iter(valores))
        otimo = otimos[(qid, n, W)]
        delta = otimo - valor
        if delta < 0:
            raise ValueError(f"Valor > DP: {chave}")
        redund = redundancia(list(ids), indice_textos)
        saida.append({
            "query_id": qid, "n": n, "W": W, "estrategia": estrategia,
            "repeticoes_originais": len(grupo), "n_real": int(grupo[0]["n_real"]),
            "valor_dp_quantizado": otimo, "valor_estrategia_quantizado": valor,
            "delta_valor_quantizado": delta, "delta_valor_tfidf_aproximado": delta / 1000,
            "custo_total": custo, "uso_orcamento": custo / W if W else None,
            "n_escolhidos": len(ids), "ids_escolhidos": "|".join(ids),
            **redund,
        })
    return saida


def gravar_csv(caminho: Path, linhas: list[dict]) -> None:
    if not linhas:
        raise ValueError("Tentativa de gerar CSV vazio")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)


def medir_preprocessamento(caminho: Path, reps: int, aquecimentos: int) -> dict:
    valores = []
    for i in range(-aquecimentos, reps):
        t0 = time.perf_counter_ns()
        chunks = carregar_chunks(caminho)
        build_statistics(chunks)
        tempo = time.perf_counter_ns() - t0
        if i >= 0:
            valores.append(tempo)
    return {"amostras_ns": valores, "mediana_ns": statistics.median(valores)}


def fluxo(query: str, chunks, estatisticas, n: int, W: int, estrategia: str) -> dict:
    """Cronometria real do fluxo completo DE CONSULTA, sem ingestao."""
    t0 = time.perf_counter_ns()
    resultados = retrieve(query, chunks, estatisticas, k=n, algoritmo="merge")
    t1 = time.perf_counter_ns()
    itens = itens_de_resultados(resultados)
    t2 = time.perf_counter_ns()
    selecao = ESTRATEGIAS[estrategia](itens, W)
    t3 = time.perf_counter_ns()
    return {
        "n_real": len(itens), "ids_escolhidos": selecao.ids,
        "valor_quantizado": selecao.valor_total, "custo_total": selecao.custo_total,
        "tempo_recuperacao_ns": t1 - t0, "tempo_conversao_ns": t2 - t1,
        "tempo_selecao_ns": t3 - t2, "tempo_fluxo_consulta_ns": t3 - t0,
    }


def medir_fluxos(consultas, chunks, estatisticas, casos, repeticoes, aquecimentos, saida):
    rng = random.Random(SEMENTE)
    medidos = 0
    with saida.open("w", encoding="utf-8") as f:
        for indice, (qid, n, W) in enumerate(casos, 1):
            for rep in range(-aquecimentos, repeticoes):
                ordem = list(NOMES_PRINCIPAIS)
                rng.shuffle(ordem)
                for estrategia in ordem:
                    resultado = fluxo(consultas[qid], chunks, estatisticas, n, W, estrategia)
                    if rep < 0:
                        continue
                    if resultado["custo_total"] > W:
                        raise AssertionError("Excesso de orcamento")
                    linha = {"query_id": qid, "n": n, "W": W,
                             "estrategia": estrategia, "repeticao": rep + 1, **resultado}
                    f.write(json.dumps(linha, ensure_ascii=False) + "\n")
                    medidos += 1
            if indice % 9 == 0 or indice == len(casos):
                print(f"Fluxo C3+conversao+selecao: {indice}/{len(casos)} cenarios", flush=True)
    return medidos


def resumir_fluxos(registros: list[dict]) -> list[dict]:
    grupos = defaultdict(list)
    for r in registros:
        grupos[(int(r["n"]), int(r["W"]), r["estrategia"])].append(r)
    linhas = []
    for (n, W, est), grupo in sorted(grupos.items()):
        linhas.append({
            "n": n, "W": W, "estrategia": est, "medicoes": len(grupo),
            **{f"mediana_{nome}_ms": statistics.median(r[f"tempo_{nome}_ns"] for r in grupo) / 1e6
               for nome in ("recuperacao", "conversao", "selecao", "fluxo_consulta")},
        })
    return linhas


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rapido", action="store_true", help="3 consultas; 1 repeticao; sem aquecimentos; arquivos separados")
    p.add_argument("--somente-metricas", action="store_true", help="gera Delta V e redundancia sem executar fluxo")
    p.add_argument("--repeticoes", type=int, default=3)
    p.add_argument("--aquecimentos", type=int, default=1)
    args = p.parse_args()
    if args.repeticoes < 1 or args.aquecimentos < 0:
        p.error("repeticoes >= 1; aquecimentos >= 0")
    if not BRUTOS.exists():
        p.error("Nao existe a execucao original: experimentos/av2/brutos/execucoes.jsonl")
    originais = ler_jsonl(BRUTOS)
    consultas = ler_consultas()
    corpus = corpus_efetivo()
    hashes = hash_corpus()
    if hashes["equivalencia_corpus"] is False:
        raise ValueError("Corpus versionado e corpus processado diferem (SHA-256); investigue antes de medir")
    chunks = carregar_chunks(corpus)
    indice_textos = {c.chunk_id: c.texto for c in chunks}
    if len(indice_textos) != len(chunks):
        raise ValueError("IDs duplicados no corpus")
    itens = calcular_metricas_complementares(originais, indice_textos)
    sufixo = "_rapido" if args.rapido else ""
    csv_metricas = BASE / "processados" / f"metricas_complementares{sufixo}.csv"
    if args.rapido:
        itens = [r for r in itens if r["query_id"] in list(consultas)[:3]]
    gravar_csv(csv_metricas, itens)
    print(f"Metricas de Delta V e redundancia: {len(itens)} linhas -> {csv_metricas.relative_to(RAIZ)}")
    if args.somente_metricas:
        return 0

    # O tempo de ingestao e medido independentemente; o fluxo parte do corpus
    # e das estatisticas ja preparados (mesmo limite das 6750 medicoes originais).
    repeticoes = 1 if args.rapido else args.repeticoes
    aquecimentos = 0 if args.rapido else args.aquecimentos
    preparo = medir_preprocessamento(corpus, repeticoes, aquecimentos)
    estatisticas = build_statistics(chunks)
    casos = sorted({(r["query_id"], r["n"], r["W"]) for r in itens})
    # Opcao --rapido usa apenas as 3 consultas, mas mantem a grade n x W.
    bruto_fluxo = BASE / "brutos" / f"fluxo_completo{sufixo}.jsonl"
    qtd = medir_fluxos(consultas, chunks, estatisticas, casos, repeticoes, aquecimentos, bruto_fluxo)
    registros_fluxo = ler_jsonl(bruto_fluxo)
    if qtd != len(casos) * len(NOMES_PRINCIPAIS) * repeticoes:
        raise AssertionError("Quantidade de registros do fluxo divergente")
    original = {(r["query_id"], r["n"], r["W"], r["estrategia"]): r for r in itens}
    for r in registros_fluxo:
        key = (r["query_id"], r["n"], r["W"], r["estrategia"])
        anterior = original[key]
        ids_esperados = anterior["ids_escolhidos"].split("|") if anterior["ids_escolhidos"] else []
        if r["ids_escolhidos"] != ids_esperados:
            raise AssertionError(f"Diferenca no conjunto selecionado: {key}")
        if r["valor_quantizado"] != anterior["valor_estrategia_quantizado"]:
            raise AssertionError(f"Valor diferente entre medicoes: {key}")
    resumo = BASE / "processados" / f"resumo_fluxo{sufixo}.csv"
    gravar_csv(resumo, resumir_fluxos(registros_fluxo))
    metadata = {
        "gerado_utc": datetime.now(timezone.utc).isoformat(),
        "commit_base": subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ,
                                      capture_output=True, text=True).stdout.strip(),
        "python": platform.python_version(), "plataforma": platform.platform(),
        "nucleos_logicos": os.cpu_count(), "semente": SEMENTE,
        "comparacao_principal": list(NOMES_PRINCIPAIS),
        "repeticoes": repeticoes, "aquecimentos": aquecimentos,
        "cenarios": len(casos), "medicoes_fluxo": qtd,
        "preprocessamento_ns": preparo,
        "hashes_corpus": hashes,
        "metodo_redundancia": "Jaccard de conjuntos de palavras (casefold/split); pares >= 0.8",
        "escopo_fluxo": "C3 retrieve + conversao + selecao; corpus e estatisticas precomputados",
        "nota": "Novas medicoes separadas das 6750 execucoes originais; maquinas/horarios diferem",
    }
    logfile = BASE / "logs" / f"ambiente_complementar{sufixo}.json"
    logfile.parent.mkdir(parents=True, exist_ok=True)
    logfile.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fluxo completo de consulta: {qtd} medicoes; {len(casos)} cenarios")
    print(f"Resumo: {resumo.relative_to(RAIZ)}")
    print(f"SHA corpus: {metadata['hashes_corpus']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
