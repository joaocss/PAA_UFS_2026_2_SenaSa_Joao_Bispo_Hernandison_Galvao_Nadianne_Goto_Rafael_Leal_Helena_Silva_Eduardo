from paa_context.relevance import relevance_score


def test_relevancia_total():
    query = "lista python"
    chunk = "Uma lista em Python pode armazenar valores."

    assert relevance_score(query, chunk) == 1.0


def test_relevancia_parcial():
    query = "lista python funcao"
    chunk = "Uma lista em Python pode armazenar valores."

    assert relevance_score(query, chunk) == 2 / 3


def test_sem_relevancia():
    query = "lista python"
    chunk = "Operadores booleanos representam verdadeiro ou falso."

    assert relevance_score(query, chunk) == 0.0


def test_query_vazia():
    assert relevance_score("", "qualquer texto") == 0.0


def test_termos_repetidos():
    query = "lista lista lista python"
    chunk = "Uma lista em Python."

    assert relevance_score(query, chunk) == 1.0