"""Calcula o gabarito dos fixtures pela formula do contrato 02, de forma independente.

Este script e o oraculo dos testes de equivalencia: implementa a formula do jeito
mais literal possivel, sem reaproveitar nada de src/, para que um erro em
pontuacao.py nao se repita aqui. Rodar da raiz do repositorio:

    python tests/fixtures/calcular_gabarito.py

Regera tests/fixtures/esperado_<query_id>.json com os 5 melhores de cada consulta.
"""

from __future__ import annotations

import csv
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

K = 5
PASTA = Path(__file__).parent


def tokenizar(texto: str) -> list[str]:
    """Token = sequencia de letras e digitos, em minusculas e sem acentos.

    Mesmo criterio do normalize de src/paa_context/preprocessing.py, escrito de
    outro jeito (regex em vez de isalnum) para nao copiar o codigo testado.
    """
    decomposto = unicodedata.normalize("NFD", texto.lower())
    sem_acentos = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return re.findall(r"[^\W_]+", sem_acentos)


def main() -> None:
    chunks = [json.loads(l) for l in (PASTA / "chunks_sinteticos.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    n_chunks = len(chunks)
    contagens = {c["chunk_id"]: Counter(tokenizar(c["texto"])) for c in chunks}
    df: Counter = Counter()
    for cont in contagens.values():
        df.update(cont.keys())

    def idf(termo: str) -> float:
        return math.log((n_chunks + 1) / (df[termo] + 1)) + 1

    def tf(termo: str, cont: Counter) -> float:
        f = cont[termo]
        return 1 + math.log(f) if f > 0 else 0.0

    with (PASTA / "consultas_sinteticas.csv").open(encoding="utf-8") as arq:
        consultas = list(csv.DictReader(arq))

    for consulta in consultas:
        qtf = Counter(tokenizar(consulta["texto"]))
        candidatos = []
        for c in chunks:
            cont = contagens[c["chunk_id"]]
            escore = sum(qtf[t] * tf(t, cont) * idf(t) for t in qtf)
            if escore > 0:
                candidatos.append((c["chunk_id"], c["source_order"], escore))
        # ordem total do contrato 02: maior escore, depois menor source_order
        candidatos.sort(key=lambda x: (-x[2], x[1]))
        topo = [{"chunk_id": cid, "escore": round(esc, 6)} for cid, _, esc in candidatos[:K]]
        saida = PASTA / f"esperado_{consulta['query_id']}.json"
        saida.write_text(json.dumps({"query_id": consulta["query_id"], "consulta": consulta["texto"], "k": K, "resultados": topo}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{consulta['query_id']} ({consulta['texto']}): {len(candidatos)} candidatos")
        for i, (cid, so, esc) in enumerate(candidatos[:K], 1):
            print(f"  {i}. {cid:16s} source_order={so:2d} escore={esc:.6f}")


if __name__ == "__main__":
    main()
