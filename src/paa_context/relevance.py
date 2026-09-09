from .preprocessing import normalize


def relevance_score(query, chunk):
    query_terms = set(normalize(query))
    chunk_terms = set(normalize(chunk))

    if not query_terms:
        return 0.0

    common = query_terms & chunk_terms

    return len(common) / len(query_terms)