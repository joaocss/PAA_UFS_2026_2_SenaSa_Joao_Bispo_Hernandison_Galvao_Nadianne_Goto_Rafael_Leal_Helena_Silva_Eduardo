import math
from collections import Counter

from .estatisticas import Estatisticas
from .preprocessing import normalize


def build_statistics(chunks):
    """Conta N e o df de cada termo, uma vez so, antes das consultas.

    df conta em quantos chunks o termo aparece, nao quantas vezes.

    Tempo: Theta(T), com T = total de tokens do corpus.
    """
    df = Counter()

    for chunk in chunks:
        df.update(set(normalize(chunk.texto)))

    return Estatisticas(n_chunks=len(chunks), df=dict(df))


def relevance_score(query, chunk, estatisticas):
    """Escore tf-idf do chunk para a consulta (contrato 02).

    tf = 1 + ln f se o termo ocorre no chunk, senao 0.
    idf = ln((N + 1) / (df + 1)) + 1.
    score = soma de qtf * tf * idf sobre os termos distintos da consulta.

    Tempo: Theta(m + n), com m tokens na consulta e n tokens no chunk.
    """
    query_terms = Counter(normalize(query))
    chunk_terms = Counter(normalize(chunk.texto))

    if not query_terms:
        return 0.0

    score = 0.0

    for term, qtf in query_terms.items():
        f = chunk_terms[term]
        if f == 0:
            continue
        tf = 1 + math.log(f)
        idf = math.log((estatisticas.n_chunks + 1) / (estatisticas.df.get(term, 0) + 1)) + 1
        score += qtf * tf * idf

    return score
