"""Gera tabelas e figuras a partir de experimentos/brutos/execucoes.jsonl.

Uso:
    python scripts/gerar_figuras.py

Tabelas em experimentos/processados/ (CSV e Markdown), figuras em
experimentos/figuras/. Estatistica por celula: mediana e intervalo
interquartil (IQR), conforme o protocolo.

Qualidade da recuperacao: se data/qrels.csv existir, calcula Precision@k,
Recall@k, nDCG@k e MRR. Independente dele, calcula um indicador auxiliar,
`na_secao@k`: a fracao do top-k que cai na secao esperada de data/queries.csv.
Esse indicador nao substitui o julgamento humano; serve para leitura rapida.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.metricas import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank  # noqa: E402
from paa_context.modelos import carregar_chunks  # noqa: E402

BRUTOS = RAIZ / "experimentos" / "brutos" / "execucoes.jsonl"
PROCESSADOS = RAIZ / "experimentos" / "processados"
FIGURAS = RAIZ / "experimentos" / "figuras"
CHUNKS = RAIZ / "data" / "processed" / "chunks.jsonl"
CONSULTAS = RAIZ / "data" / "queries.csv"
QRELS = RAIZ / "data" / "qrels.csv"

CONFIGS = ["C1", "C2", "C3", "C4"]
CORES = {"C1": "#b5541b", "C2": "#2f6f4f", "C3": "#6b4c9a", "C4": "#7a7a7a"}
ROTULOS = {
    "C1": "C1 varredura + Insertion",
    "C2": "C2 índice + busca binária + Merge",
    "C3": "C3 varredura + Merge",
    "C4": "C4 scikit-learn (referência)",
}


def mediana_iqr(valores):
    valores = sorted(v for v in valores if v is not None)
    if not valores:
        return None, None
    if len(valores) < 2:
        return valores[0], 0
    q1, _, q3 = statistics.quantiles(valores, n=4, method="inclusive")
    return statistics.median(valores), q3 - q1


def gravar(nome, cabecalho, linhas):
    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    with (PROCESSADOS / f"{nome}.csv").open("w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida, lineterminator="\n")
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)
    texto = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join("---" for _ in cabecalho) + " |"]
    texto += ["| " + " | ".join(str(c) for c in linha) + " |" for linha in linhas]
    (PROCESSADOS / f"{nome}.md").write_text("\n".join(texto) + "\n", encoding="utf-8")


def ms(ns):
    return None if ns is None else round(ns / 1e6, 2)


def tabela_desempenho(execucoes):
    grupos = defaultdict(list)
    for e in execucoes:
        grupos[(e["config"], e["tamanho_corpus"])].append(e)

    cabecalho = [
        "config", "tamanho_%", "n_chunks", "execucoes",
        "total_ms", "total_iqr_ms", "ingestao_ms", "indice_ms", "busca_ms", "ordenacao_ms", "consulta_ms",
        "comparacoes", "comparacoes_iqr", "trocas", "candidatos_P", "memoria_pico_kib", "vazios_%",
    ]
    linhas = []
    for config in CONFIGS:
        for tamanho in sorted({t for c, t in grupos if c == config}):
            g = grupos[(config, tamanho)]
            total, total_iqr = mediana_iqr(e["tempo_total_ns"] for e in g)
            comp, comp_iqr = mediana_iqr(e["comparacoes"] for e in g)
            linhas.append([
                config, tamanho, g[0]["n_chunks"], len(g),
                ms(total), ms(total_iqr),
                ms(mediana_iqr(e["tempo_ingestao_ns"] for e in g)[0]),
                ms(mediana_iqr(e["tempo_indice_ns"] for e in g)[0]),
                ms(mediana_iqr(e["tempo_busca_ns"] for e in g)[0]),
                ms(mediana_iqr(e["tempo_ordenacao_ns"] for e in g)[0]),
                ms(mediana_iqr(e["tempo_consulta_ns"] for e in g)[0]),
                comp if comp is None else round(comp), comp_iqr if comp_iqr is None else round(comp_iqr),
                mediana_iqr(e["trocas"] for e in g)[0],
                round(mediana_iqr(e["n_candidatos"] for e in g)[0]),
                round(mediana_iqr(e["memoria_pico_bytes"] for e in g)[0] / 1024),
                round(100 * sum(e["resultado_vazio"] for e in g) / len(g), 1),
            ])
    gravar("desempenho_por_configuracao", cabecalho, linhas)
    return linhas


def figura_comparacoes_por_tamanho(execucoes):
    fig, eixo = plt.subplots(figsize=(7, 4.5))
    for config in ["C1", "C2", "C3"]:
        por_tamanho = defaultdict(list)
        for e in execucoes:
            if e["config"] == config:
                por_tamanho[e["n_chunks"]].append(e["comparacoes"])
        xs = sorted(por_tamanho)
        eixo.plot(xs, [statistics.median(por_tamanho[x]) for x in xs], marker="o", color=CORES[config], label=ROTULOS[config])
    eixo.set_xscale("log")
    eixo.set_yscale("log")
    eixo.set_xlabel("chunks no corpus (N)")
    eixo.set_ylabel("comparações (mediana das consultas)")
    eixo.set_title("Comparações por tamanho do corpus")
    eixo.grid(True, which="both", alpha=0.3)
    eixo.legend()
    fig.tight_layout()
    fig.savefig(FIGURAS / "comparacoes_por_tamanho.png", dpi=150)
    plt.close(fig)


def figura_comparacoes_por_candidatos(execucoes):
    fig, eixo = plt.subplots(figsize=(7, 4.5))
    maior_p = 1
    for config in ["C1", "C3"]:
        pontos = [(e["n_candidatos"], e["comparacoes"]) for e in execucoes if e["config"] == config and e["repeticao"] == 1 and e["k"] == 5]
        maior_p = max([maior_p] + [p for p, _ in pontos])
        eixo.scatter([p for p, _ in pontos], [c for _, c in pontos], s=12, alpha=0.6, color=CORES[config], label=ROTULOS[config])
    import math

    ps = [p for p in range(2, maior_p + 1, max(1, maior_p // 200))]
    eixo.plot(ps, [p * p / 4 for p in ps], color=CORES["C1"], linestyle="--", linewidth=1, label="P²/4 (Insertion, caso médio)")
    eixo.plot(ps, [p * math.log2(p) for p in ps], color=CORES["C3"], linestyle="--", linewidth=1, label="P log₂ P (Merge)")
    eixo.set_xscale("log")
    eixo.set_yscale("log")
    eixo.set_xlabel("candidatos com escore > 0 (P)")
    eixo.set_ylabel("comparações")
    eixo.set_title("Comparações medidas contra a previsão assintótica")
    eixo.grid(True, which="both", alpha=0.3)
    eixo.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURAS / "comparacoes_por_candidatos.png", dpi=150)
    plt.close(fig)


def figura_tempo(execucoes):
    fig, eixo = plt.subplots(figsize=(7, 4.5))
    for config in CONFIGS:
        por_tamanho = defaultdict(list)
        for e in execucoes:
            if e["config"] == config:
                por_tamanho[e["n_chunks"]].append(e["tempo_total_ns"] / 1e6)
        xs = sorted(por_tamanho)
        eixo.plot(xs, [statistics.median(por_tamanho[x]) for x in xs], marker="o", color=CORES[config], label=ROTULOS[config])
    eixo.set_xlabel("chunks no corpus (N)")
    eixo.set_ylabel("tempo total por execução (ms, mediana)")
    eixo.set_title("Tempo total por tamanho do corpus")
    eixo.grid(True, alpha=0.3)
    eixo.legend()
    fig.tight_layout()
    fig.savefig(FIGURAS / "tempo_por_tamanho.png", dpi=150)
    plt.close(fig)


def figura_decomposicao(execucoes):
    maior = max(e["tamanho_corpus"] for e in execucoes)
    partes = [("tempo_ingestao_ns", "ingestão (N, df)"), ("tempo_indice_ns", "construção do índice"), ("tempo_busca_ns", "busca e pontuação"), ("tempo_ordenacao_ns", "ordenação")]
    tons = ["#d9d4c7", "#9c8f6e", "#4f5d48", "#b5541b"]
    fig, eixo = plt.subplots(figsize=(7, 4.5))
    base = [0.0] * len(CONFIGS)
    for (campo, rotulo), tom in zip(partes, tons):
        valores = [statistics.median(e[campo] / 1e6 for e in execucoes if e["config"] == c and e["tamanho_corpus"] == maior) for c in CONFIGS]
        eixo.bar(CONFIGS, valores, bottom=base, color=tom, label=rotulo)
        base = [b + v for b, v in zip(base, valores)]
    eixo.set_ylabel("ms (mediana)")
    eixo.set_title(f"Onde o tempo vai, corpus a {maior} %")
    eixo.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURAS / "decomposicao_do_tempo.png", dpi=150)
    plt.close(fig)


def listas_por_consulta(execucoes):
    """(config, tamanho, k, query_id) -> ids devolvidos. A lista nao muda entre repeticoes."""
    return {(e["config"], e["tamanho_corpus"], e["k"], e["query_id"]): e["resultado_ids"] for e in execucoes if e["repeticao"] == 1}


def tabela_qualidade(execucoes, consultas):
    listas = listas_por_consulta(execucoes)
    categoria = {q["query_id"]: q["categoria"] for q in consultas}
    maior = max(e["tamanho_corpus"] for e in execucoes)
    ids_consultas = sorted({q for _, t, _, q in listas if t == maior})

    # Indicador auxiliar: fracao do top-k na secao esperada.
    chunks = {c.chunk_id: c for c in carregar_chunks(CHUNKS)}
    esperado = {q["query_id"]: (q["capitulo_esperado"], set(q["secao_esperada"].split("|"))) for q in consultas}

    def na_secao(chunk_id, query_id):
        capitulo, secoes = esperado[query_id]
        chunk = chunks[chunk_id]
        return Path(chunk.arquivo).stem == capitulo and chunk.secao in secoes

    qrels = defaultdict(dict)
    if QRELS.exists():
        for linha in csv.DictReader(QRELS.open(encoding="utf-8")):
            qrels[linha["query_id"]][linha["chunk_id"]] = int(linha["adjudicada"] or linha["relevancia"])

    cabecalho = ["config", "k", "categoria", "consultas", "na_secao@k"]
    if qrels:
        cabecalho += ["P@k", "R@k", "nDCG@k", "MRR"]
    linhas = []
    for config in CONFIGS:
        for k in sorted({k for _, _, k, _ in listas}):
            for cat in ["todas", "facil", "media", "dificil"]:
                qs = [q for q in ids_consultas if (config, maior, k, q) in listas and (cat == "todas" or categoria[q] == cat)]
                if not qs:
                    continue
                aux = statistics.mean(sum(na_secao(i, q) for i in listas[(config, maior, k, q)]) / k for q in qs)
                linha = [config, k, cat, len(qs), round(aux, 3)]
                if qrels:
                    def media(valores):
                        valores = [v for v in valores if v is not None]
                        return round(statistics.mean(valores), 3) if valores else None
                    linha += [
                        media(precision_at_k(listas[(config, maior, k, q)], qrels[q], k) for q in qs),
                        media(recall_at_k(listas[(config, maior, k, q)], qrels[q], k) for q in qs),
                        media(ndcg_at_k(listas[(config, maior, k, q)], qrels[q], k) for q in qs),
                        media(reciprocal_rank(listas[(config, maior, k, q)], qrels[q]) for q in qs),
                    ]
                linhas.append(linha)
    gravar("qualidade_por_configuracao", cabecalho, linhas)

    # Sobreposicao da referencia (C4) com a lista da equipe (C1 = C2 = C3).
    sobreposicao = []
    for k in sorted({k for _, _, k, _ in listas}):
        valores = [len(set(listas[("C4", maior, k, q)]) & set(listas[("C1", maior, k, q)])) / k for q in ids_consultas if ("C4", maior, k, q) in listas]
        if valores:
            sobreposicao.append([k, len(valores), round(statistics.mean(valores), 3)])
    gravar("sobreposicao_c4_c1", ["k", "consultas", "fracao_do_topk_em_comum"], sobreposicao)
    return bool(qrels)


def tabela_secoes_mais_devolvidas(execucoes):
    listas = listas_por_consulta(execucoes)
    maior = max(e["tamanho_corpus"] for e in execucoes)
    chunks = {c.chunk_id: c for c in carregar_chunks(CHUNKS)}
    for config in ["C1", "C4"]:
        contagem = defaultdict(int)
        total = 0
        for (c, t, k, _), ids in listas.items():
            if c == config and t == maior and k == 10:
                for i in ids:
                    contagem[chunks[i].secao or "(sem seção)"] += 1
                    total += 1
        linhas = [[secao, n, round(100 * n / total, 1)] for secao, n in sorted(contagem.items(), key=lambda x: -x[1])[:10]]
        gravar(f"secoes_mais_devolvidas_{config}", ["secao", "vezes_no_top10", "%"], linhas)


def principal() -> int:
    if not BRUTOS.exists():
        print(f"nao encontrei {BRUTOS}. Rode antes: python scripts/rodar_experimentos.py", file=sys.stderr)
        return 1
    execucoes = [json.loads(linha) for linha in BRUTOS.open(encoding="utf-8")]
    consultas = list(csv.DictReader(CONSULTAS.open(encoding="utf-8")))
    FIGURAS.mkdir(parents=True, exist_ok=True)

    tabela_desempenho(execucoes)
    com_qrels = tabela_qualidade(execucoes, consultas)
    tabela_secoes_mais_devolvidas(execucoes)
    figura_comparacoes_por_tamanho(execucoes)
    figura_comparacoes_por_candidatos(execucoes)
    figura_tempo(execucoes)
    figura_decomposicao(execucoes)

    print(f"{len(execucoes)} execucoes lidas; tabelas em {PROCESSADOS.relative_to(RAIZ)}, figuras em {FIGURAS.relative_to(RAIZ)}")
    if not com_qrels:
        print("data/qrels.csv ainda nao existe: P@k, R@k, nDCG@k e MRR ficam de fora")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
