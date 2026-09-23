"""Mede o tempo real de ingestao e roda o experimento de sensibilidade ao tamanho do chunk.

Uso:
    python scripts/medir_ingestao.py
    python scripts/medir_ingestao.py --rapido     # 1 repeticao, sem aquecimento

Complementa scripts/rodar_experimentos.py em dois pontos.

1. Tempo de pre-processamento/ingestao (secao 7.3 do enunciado). O campo
   tempo_ingestao_ns do experimento principal mede so as estatisticas do
   corpus (N e df). Aqui entra a ingestao de fato: leitura dos 21 notebooks,
   extracao das celulas, normalizacao e fragmentacao, separadas em duas
   parcelas. O download fica de fora, porque depende da rede.

2. Sensibilidade ao tamanho do chunk, prevista em data/README.md: 128/16,
   256/32 (configuracao principal) e 512/64. Para cada uma, registra quantos
   chunks saem, o tamanho deles, e, sobre as 30 consultas de data/queries.csv
   no corpus inteiro, candidatos (P), comparacoes de C1 e C3 e o indicador
   auxiliar na_secao@10 do top-10. Comparacoes e na_secao nao dependem da
   maquina; os tempos dependem.

Estatistica: mediana e intervalo interquartil de 5 medidas, depois de 2
aquecimentos descartados, como no protocolo.

Saidas: experimentos/processados/ingestao_e_sensibilidade.{csv,md} e
experimentos/logs/ambiente_ingestao.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import socket
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from paa_context.contador import Contador  # noqa: E402
from paa_context.fragmentacao import extrair_celulas, fragmentar  # noqa: E402
from paa_context.insertion_sort import insertion_sort  # noqa: E402
from paa_context.linear_search import linear_search  # noqa: E402
from paa_context.merge_sort import merge_sort  # noqa: E402
from paa_context.pipeline import top_k  # noqa: E402
from paa_context.relevance import build_statistics  # noqa: E402
from preparar_corpus import PASTA_BRUTA, notebooks_na_ordem  # noqa: E402
from rodar_experimentos import commit_atual, sysctl, versao  # noqa: E402

CONSULTAS = RAIZ / "data" / "queries.csv"
PROCESSADOS = RAIZ / "experimentos" / "processados"
AMBIENTE = RAIZ / "experimentos" / "logs" / "ambiente_ingestao.json"

CONFIGURACOES_CHUNK = [(128, 16), (256, 32), (512, 64)]
REPETICOES = 5
AQUECIMENTOS = 2
K = 10


def mediana_iqr(valores):
    valores = sorted(valores)
    if len(valores) < 2:
        return valores[0], 0
    q1, _, q3 = statistics.quantiles(valores, n=4, method="inclusive")
    return statistics.median(valores), q3 - q1


def ms(ns):
    return round(ns / 1e6, 2)


def numero(valor):
    """Mediana sem o '.0' quando e inteira, para a tabela ficar legivel."""
    return int(valor) if float(valor).is_integer() else valor


def ingerir(caminhos, tamanho, sobreposicao):
    """Uma ingestao completa. Devolve (chunks, ns de extracao, ns de fragmentacao)."""
    t0 = time.perf_counter_ns()
    celulas = []
    for caminho in caminhos:
        celulas.extend(extrair_celulas(caminho, raiz=PASTA_BRUTA))
    t1 = time.perf_counter_ns()
    chunks = fragmentar(celulas, tamanho=tamanho, sobreposicao=sobreposicao)
    t2 = time.perf_counter_ns()
    return chunks, t1 - t0, t2 - t1


def custo_e_qualidade(chunks, consultas):
    """Por consulta: P, comparacoes de C1 e C3 e na_secao@K. Devolve as medianas e a media de na_secao."""
    estatisticas = build_statistics(chunks)
    candidatos, comp_c1, comp_c3, na_secao = [], [], [], []
    for consulta in consultas:
        pontuados = linear_search(consulta["texto"], chunks, estatisticas)
        contador_c1, contador_c3 = Contador(), Contador()
        lista_c1 = top_k(insertion_sort(pontuados, contador=contador_c1), K)
        lista_c3 = top_k(merge_sort(pontuados, contador=contador_c3), K)
        if [c.chunk_id for c, _ in lista_c1] != [c.chunk_id for c, _ in lista_c3]:
            raise SystemExit(f"C1 e C3 divergiram em {consulta['query_id']}: bug, nao resultado")
        secoes = set(consulta["secao_esperada"].split("|"))
        acertos = sum(Path(c.arquivo).stem == consulta["capitulo_esperado"] and c.secao in secoes for c, _ in lista_c3)
        candidatos.append(len(pontuados))
        comp_c1.append(contador_c1.comparacoes)
        comp_c3.append(contador_c3.comparacoes)
        na_secao.append(acertos / K)
    return (
        numero(statistics.median(candidatos)),
        numero(statistics.median(comp_c1)),
        numero(statistics.median(comp_c3)),
        round(statistics.mean(na_secao), 3),
    )


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opcoes.add_argument("--rapido", action="store_true", help="1 repeticao, sem aquecimento")
    args = opcoes.parse_args()

    caminhos = notebooks_na_ordem(None)
    consultas = list(csv.DictReader(CONSULTAS.open(encoding="utf-8")))
    repeticoes, aquecimentos = (1, 0) if args.rapido else (REPETICOES, AQUECIMENTOS)
    inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")

    cabecalho = [
        "tamanho", "sobreposicao", "n_chunks", "tokens_mediana", "tokens_max", "chunks_de_celula_cortada_%",
        "extracao_ms", "fragmentacao_ms", "ingestao_ms", "ingestao_iqr_ms",
        "candidatos_P", "comparacoes_C1", "comparacoes_C3", "na_secao@10",
    ]
    linhas = []
    for tamanho, sobreposicao in CONFIGURACOES_CHUNK:
        extracao, fragmentacao, total = [], [], []
        for repeticao in range(-aquecimentos, repeticoes):
            chunks, ns_extracao, ns_fragmentacao = ingerir(caminhos, tamanho, sobreposicao)
            if repeticao < 0:
                continue
            extracao.append(ns_extracao)
            fragmentacao.append(ns_fragmentacao)
            total.append(ns_extracao + ns_fragmentacao)

        tokens = [c.n_tokens for c in chunks]
        por_celula = Counter((c.arquivo, c.celula_idx) for c in chunks)
        cortados = sum(1 for c in chunks if por_celula[(c.arquivo, c.celula_idx)] > 1)
        ingestao, ingestao_iqr = mediana_iqr(total)
        candidatos, comp_c1, comp_c3, na_secao = custo_e_qualidade(chunks, consultas)
        linhas.append([
            tamanho, sobreposicao, len(chunks), numero(statistics.median(tokens)), max(tokens),
            round(100 * cortados / len(chunks), 1),
            ms(statistics.median(extracao)), ms(statistics.median(fragmentacao)), ms(ingestao), ms(ingestao_iqr),
            candidatos, comp_c1, comp_c3, na_secao,
        ])
        print(f"{tamanho}/{sobreposicao}: {len(chunks)} chunks, ingestao {ms(ingestao)} ms, "
              f"P {candidatos}, comparacoes C1 {comp_c1} e C3 {comp_c3}, na_secao@10 {na_secao}", flush=True)

    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    with (PROCESSADOS / "ingestao_e_sensibilidade.csv").open("w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida, lineterminator="\n")
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)
    texto = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join("---" for _ in cabecalho) + " |"]
    texto += ["| " + " | ".join(str(c) for c in linha) + " |" for linha in linhas]
    (PROCESSADOS / "ingestao_e_sensibilidade.md").write_text("\n".join(texto) + "\n", encoding="utf-8")

    memoria = sysctl("hw.memsize")
    ambiente = {
        "inicio": inicio,
        "fim": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": commit_atual(),
        "comando": " ".join([Path(sys.executable).name] + sys.argv),
        "argumentos": vars(args),
        "host": socket.gethostname(),
        "sistema": platform.platform(),
        "processador": sysctl("machdep.cpu.brand_string") or platform.processor(),
        "nucleos": os.cpu_count(),
        "memoria_bytes": int(memoria) if memoria else None,
        "python": platform.python_version(),
        "bibliotecas": {p: versao(p) for p in ["scikit-learn", "numpy", "scipy", "matplotlib"]},
        "repeticoes": repeticoes,
        "aquecimentos": aquecimentos,
    }
    AMBIENTE.parent.mkdir(parents=True, exist_ok=True)
    AMBIENTE.write_text(json.dumps(ambiente, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"tabela em {(PROCESSADOS / 'ingestao_e_sensibilidade.md').relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
