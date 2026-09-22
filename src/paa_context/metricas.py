"""Metricas de qualidade da recuperacao, a partir dos julgamentos (qrels).

`relevancia` e um dicionario chunk_id -> grau (0, 1 ou 2), com os chunks
julgados para uma consulta. Chunk nao julgado conta como grau 0.
Um chunk e considerado relevante quando o grau e >= 1.
"""

import math


def _relevantes(relevancia):
    return {chunk_id for chunk_id, grau in relevancia.items() if grau >= 1}


def precision_at_k(ids, relevancia, k):
    """Fracao dos k primeiros que e relevante. Divide por k, mesmo se vierem menos resultados."""
    if k <= 0:
        return 0.0
    relevantes = _relevantes(relevancia)
    return sum(1 for chunk_id in ids[:k] if chunk_id in relevantes) / k


def recall_at_k(ids, relevancia, k):
    """Fracao dos relevantes julgados que aparece nos k primeiros. None se nao ha relevante."""
    relevantes = _relevantes(relevancia)
    if not relevantes:
        return None
    return sum(1 for chunk_id in ids[:k] if chunk_id in relevantes) / len(relevantes)


def ndcg_at_k(ids, relevancia, k):
    """nDCG com ganho igual ao grau e desconto log2(posicao + 1). None se nao ha relevante."""
    ideal = sorted((grau for grau in relevancia.values() if grau > 0), reverse=True)[:k]
    if not ideal:
        return None
    dcg = sum(relevancia.get(chunk_id, 0) / math.log2(i + 2) for i, chunk_id in enumerate(ids[:k]))
    idcg = sum(grau / math.log2(i + 2) for i, grau in enumerate(ideal))
    return dcg / idcg


def reciprocal_rank(ids, relevancia):
    """1 / posicao do primeiro relevante; 0 se nenhum aparece. A media sobre consultas e o MRR."""
    relevantes = _relevantes(relevancia)
    for i, chunk_id in enumerate(ids, start=1):
        if chunk_id in relevantes:
            return 1 / i
    return 0.0
