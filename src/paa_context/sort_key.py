def sort_key(item):
    """Chave de ordenacao de um par (chunk, score), conforme docs/CONTRATOS.md.

    Chave (-score, source_order): maior score primeiro e, em empate,
    menor source_order primeiro. Quem vem antes tem a chave menor.
    """
    chunk, score = item
    return (-score, chunk.source_order)
