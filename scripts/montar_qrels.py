"""Monta os julgamentos de relevancia (data/qrels.csv) em duas etapas.

Uso:
    python scripts/montar_qrels.py pool
    python scripts/montar_qrels.py consolidar
    python scripts/montar_qrels.py importar [--gabarito CAMINHO]

A etapa `pool` junta, para cada consulta de data/queries.csv, os chunks da
secao esperada e os 10 primeiros da C3, e grava a planilha de julgamento em
data/processed/qrels_para_julgar.csv. A planilha traz o texto dos trechos e por
isso fica fora do versionamento, como o proprio corpus. A coluna `sugestao`
vale 1 para chunk da secao esperada e 0 para os demais; e so um ponto de
partida para o avaliador.

A etapa `consolidar` le a planilha preenchida (colunas `relevancia` e
`avaliador`) e grava data/qrels.csv no formato do contrato 03. Linha sem
julgamento e recusada, para que nenhuma sugestao entre como se fosse avaliacao.

A etapa `importar` e o caminho alternativo: converte o gabarito montado a mao
pela Helena (data/perguntas_30_com_chunks_justificativas.csv), que lista, para
cada consulta, os chunks que a respondem, com justificativa, escolhidos antes
de qualquer ranking ser observado. O gabarito e binario: cada chunk listado
entra com relevancia 1, e os demais contam como 0 nas metricas. Confere que
todo chunk_id existe no corpus e que a pergunta e a mesma de data/queries.csv.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.linear_search import linear_search  # noqa: E402
from paa_context.merge_sort import merge_sort  # noqa: E402
from paa_context.modelos import carregar_chunks  # noqa: E402
from paa_context.pipeline import top_k  # noqa: E402
from paa_context.relevance import build_statistics  # noqa: E402

CHUNKS = RAIZ / "data" / "processed" / "chunks.jsonl"
CONSULTAS = RAIZ / "data" / "queries.csv"
PLANILHA = RAIZ / "data" / "processed" / "qrels_para_julgar.csv"
QRELS = RAIZ / "data" / "qrels.csv"
GABARITO = RAIZ / "data" / "perguntas_30_com_chunks_justificativas.csv"
PROFUNDIDADE = 10

COLUNAS_PLANILHA = [
    "query_id", "consulta", "chunk_id", "capitulo", "secao", "n_tokens",
    "origem", "posicao_c3", "sugestao", "relevancia", "avaliador", "trecho",
]


def capitulo_do_arquivo(arquivo: str) -> str:
    """'capitulos/chap05.ipynb' -> 'chap05'."""
    return Path(arquivo).stem


def montar_pool() -> int:
    chunks = carregar_chunks(CHUNKS)
    estatisticas = build_statistics(chunks)
    consultas = list(csv.DictReader(CONSULTAS.open(encoding="utf-8")))

    linhas = []
    for consulta in consultas:
        secoes = set(consulta["secao_esperada"].split("|"))
        da_secao = {
            c.chunk_id
            for c in chunks
            if capitulo_do_arquivo(c.arquivo) == consulta["capitulo_esperado"] and c.secao in secoes
        }
        topo = top_k(merge_sort(linear_search(consulta["texto"], chunks, estatisticas)), PROFUNDIDADE)
        posicao = {chunk.chunk_id: i for i, (chunk, _) in enumerate(topo, start=1)}

        # Primeiro o que o sistema devolveu, na ordem dele; depois o resto da secao, na ordem do livro.
        ordem = [chunk for chunk, _ in topo] + [c for c in chunks if c.chunk_id in da_secao and c.chunk_id not in posicao]
        for chunk in ordem:
            na_secao = chunk.chunk_id in da_secao
            no_topo = chunk.chunk_id in posicao
            linhas.append({
                "query_id": consulta["query_id"],
                "consulta": consulta["texto"],
                "chunk_id": chunk.chunk_id,
                "capitulo": chunk.capitulo,
                "secao": chunk.secao,
                "n_tokens": chunk.n_tokens,
                "origem": "ambos" if na_secao and no_topo else ("secao" if na_secao else "top10"),
                "posicao_c3": posicao.get(chunk.chunk_id, ""),
                "sugestao": 1 if na_secao else 0,
                "relevancia": "",
                "avaliador": "",
                "trecho": chunk.texto,
            })

    # utf-8-sig para o Excel e o Google Planilhas mostrarem os acentos.
    with PLANILHA.open("w", newline="", encoding="utf-8-sig") as saida:
        escritor = csv.DictWriter(saida, fieldnames=COLUNAS_PLANILHA)
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"{len(linhas)} linhas para julgar em {PLANILHA.relative_to(RAIZ)}")
    return 0


def consolidar() -> int:
    linhas = list(csv.DictReader(PLANILHA.open(encoding="utf-8-sig")))
    faltando = [f"{l['query_id']}/{l['chunk_id']}" for l in linhas if l["relevancia"].strip() not in {"0", "1", "2"} or not l["avaliador"].strip()]
    if faltando:
        print(f"{len(faltando)} linhas sem relevancia (0, 1 ou 2) ou sem avaliador, por exemplo: {', '.join(faltando[:5])}", file=sys.stderr)
        return 1

    with QRELS.open("w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida, lineterminator="\n")
        escritor.writerow(["query_id", "chunk_id", "avaliador", "relevancia", "adjudicada"])
        for l in linhas:
            relevancia = l["relevancia"].strip()
            escritor.writerow([l["query_id"], l["chunk_id"], l["avaliador"].strip(), relevancia, relevancia])

    print(f"{len(linhas)} julgamentos gravados em {QRELS.relative_to(RAIZ)}")
    return 0


def importar(gabarito: Path) -> int:
    if not gabarito.exists():
        print(f"nao encontrei {gabarito}", file=sys.stderr)
        return 1
    ids = {c.chunk_id for c in carregar_chunks(CHUNKS)}
    perguntas = {q["query_id"]: q["texto"].strip() for q in csv.DictReader(CONSULTAS.open(encoding="utf-8"))}
    linhas = list(csv.DictReader(gabarito.open(encoding="utf-8-sig")))

    problemas = []
    vistos = set()
    for l in linhas:
        chave = (l["question_id"], l["chunk_id"])
        if l["chunk_id"] not in ids:
            problemas.append(f"{chave}: chunk_id fora do corpus")
        if perguntas.get(l["question_id"]) != l["question"].strip():
            problemas.append(f"{chave}: pergunta diferente de data/queries.csv")
        if chave in vistos:
            problemas.append(f"{chave}: repetido")
        vistos.add(chave)
    if problemas:
        print(f"{len(problemas)} problemas no gabarito, por exemplo: {'; '.join(problemas[:5])}", file=sys.stderr)
        return 1

    with QRELS.open("w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida, lineterminator="\n")
        escritor.writerow(["query_id", "chunk_id", "avaliador", "relevancia", "adjudicada"])
        for l in sorted(linhas, key=lambda l: (l["question_id"], l["chunk_id"])):
            escritor.writerow([l["question_id"], l["chunk_id"], "Helena", 1, 1])

    print(f"{len(linhas)} julgamentos de {len({l['question_id'] for l in linhas})} consultas gravados em {QRELS.relative_to(RAIZ)}")
    return 0


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opcoes.add_argument("etapa", choices=["pool", "consolidar", "importar"])
    opcoes.add_argument("--gabarito", type=Path, default=GABARITO, help="CSV do gabarito (etapa importar)")
    args = opcoes.parse_args()
    if args.etapa == "pool":
        return montar_pool()
    if args.etapa == "consolidar":
        return consolidar()
    return importar(args.gabarito)


if __name__ == "__main__":
    raise SystemExit(principal())
