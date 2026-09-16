from paa_context.linear_search import CHUNKS_PYTHON, linear_search
from paa_context.relevance import build_statistics, relevance_score

ESTATISTICAS = build_statistics(CHUNKS_PYTHON)


def test_devolve_so_candidatos():
    resultados = linear_search("lista python", CHUNKS_PYTHON, ESTATISTICAS)

    assert len(resultados) == 3
    assert all(score > 0 for _, score in resultados)


def test_preserva_ordem_do_corpus():
    resultados = linear_search("lista python", CHUNKS_PYTHON, ESTATISTICAS)
    chunks_na_saida = [chunk for chunk, _ in resultados]

    assert chunks_na_saida == [CHUNKS_PYTHON[0], CHUNKS_PYTHON[1], CHUNKS_PYTHON[3]]


def test_reutiliza_relevance_score():
    query = "lista python"
    resultados = linear_search(query, CHUNKS_PYTHON, ESTATISTICAS)

    for chunk, score in resultados:
        assert score == relevance_score(query, chunk, ESTATISTICAS)


def test_chunk_mais_relevante():
    resultados = linear_search("lista python", CHUNKS_PYTHON, ESTATISTICAS)
    scores = [score for _, score in resultados]

    assert scores[0] == max(scores)
    assert scores[1] == scores[2]


def test_relevancia_parcial():
    resultados = linear_search("lista dicionario", CHUNKS_PYTHON, ESTATISTICAS)
    chunks = [chunk for chunk, _ in resultados]
    scores = [score for _, score in resultados]

    assert chunks == [CHUNKS_PYTHON[0], CHUNKS_PYTHON[2]]
    assert scores[0] == scores[1]


def test_sem_relevancia():
    assert linear_search("recursao grafo", CHUNKS_PYTHON, ESTATISTICAS) == []


def test_consulta_vazia():
    assert linear_search("", CHUNKS_PYTHON, ESTATISTICAS) == []


def test_corpus_vazio():
    assert linear_search("lista python", [], build_statistics([])) == []
