from paa_context.linear_search import CHUNKS_PYTHON, linear_search
from paa_context.relevance import relevance_score


def test_percorre_todos_os_chunks():
    resultados = linear_search("lista python", CHUNKS_PYTHON)

    assert len(resultados) == len(CHUNKS_PYTHON)


def test_preserva_ordem_do_corpus():
    resultados = linear_search("lista python", CHUNKS_PYTHON)
    chunks_na_saida = [chunk for chunk, _ in resultados]

    assert chunks_na_saida == CHUNKS_PYTHON


def test_reutiliza_relevance_score():
    query = "lista python"
    resultados = linear_search(query, CHUNKS_PYTHON)

    for chunk, score in resultados:
        assert score == relevance_score(query, chunk)


def test_chunk_mais_relevante():
    resultados = linear_search("lista python", CHUNKS_PYTHON)
    scores = [score for _, score in resultados]

    assert scores[0] == 1.0
    assert scores == [1.0, 0.5, 0.0, 0.5, 0.0]


def test_relevancia_parcial():
    resultados = linear_search("lista dicionario", CHUNKS_PYTHON)
    scores = [score for _, score in resultados]

    assert scores[0] == 0.5
    assert scores[2] == 0.5


def test_sem_relevancia():
    resultados = linear_search("recursao grafo", CHUNKS_PYTHON)

    assert all(score == 0.0 for _, score in resultados)


def test_consulta_vazia():
    resultados = linear_search("", CHUNKS_PYTHON)

    assert all(score == 0.0 for _, score in resultados)


def test_corpus_vazio():
    assert linear_search("lista python", []) == []
