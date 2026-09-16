from paa_context.contador import Contador
from paa_context.insertion_sort import insertion_sort
from paa_context.linear_search import CHUNKS_PYTHON, linear_search
from paa_context.pipeline import retrieve, top_k
from paa_context.relevance import build_statistics, relevance_score

ESTATISTICAS = build_statistics(CHUNKS_PYTHON)


def test_top_k_zero():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON, ESTATISTICAS))

    assert top_k(ordenados, 0) == []


def test_top_k_negativo():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON, ESTATISTICAS))

    assert top_k(ordenados, -1) == []
    assert top_k(ordenados, -5) == []


def test_top_k_dois():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON, ESTATISTICAS))
    resultado = top_k(ordenados, 2)

    assert len(resultado) == 2
    assert resultado[0][0] == CHUNKS_PYTHON[0]
    assert resultado[1][0] == CHUNKS_PYTHON[1]


def test_top_k_maior_que_candidatos():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON, ESTATISTICAS))
    resultado = top_k(ordenados, 100)

    assert len(resultado) == 3
    assert all(score > 0 for _, score in resultado)
    assert [chunk for chunk, _ in resultado] == [CHUNKS_PYTHON[0], CHUNKS_PYTHON[1], CHUNKS_PYTHON[3]]


def test_top_k_exclui_score_zero():
    ordenados = [(CHUNKS_PYTHON[0], 1.0), (CHUNKS_PYTHON[2], 0.0), (CHUNKS_PYTHON[4], 0.0)]
    resultado = top_k(ordenados, 10)

    assert all(score > 0 for _, score in resultado)
    assert CHUNKS_PYTHON[2] not in [chunk for chunk, _ in resultado]
    assert CHUNKS_PYTHON[4] not in [chunk for chunk, _ in resultado]


def test_top_k_sem_candidatos():
    ordenados = insertion_sort(linear_search("recursao grafo", CHUNKS_PYTHON, ESTATISTICAS))

    assert top_k(ordenados, 5) == []


def test_retrieve_insertion():
    resultado = retrieve("lista python", CHUNKS_PYTHON, ESTATISTICAS, k=2, algoritmo="insertion")

    assert len(resultado) == 2
    assert resultado[0] == (CHUNKS_PYTHON[0], relevance_score("lista python", CHUNKS_PYTHON[0], ESTATISTICAS))
    assert resultado[1] == (CHUNKS_PYTHON[1], relevance_score("lista python", CHUNKS_PYTHON[1], ESTATISTICAS))


def test_retrieve_merge():
    resultado = retrieve("lista python", CHUNKS_PYTHON, ESTATISTICAS, k=2, algoritmo="merge")

    assert len(resultado) == 2
    assert resultado[0] == (CHUNKS_PYTHON[0], relevance_score("lista python", CHUNKS_PYTHON[0], ESTATISTICAS))
    assert resultado[1] == (CHUNKS_PYTHON[1], relevance_score("lista python", CHUNKS_PYTHON[1], ESTATISTICAS))


def test_retrieve_insertion_igual_merge():
    for k in (0, 1, 2, 3, 10, -1):
        a = retrieve("lista python", CHUNKS_PYTHON, ESTATISTICAS, k=k, algoritmo="insertion")
        b = retrieve("lista python", CHUNKS_PYTHON, ESTATISTICAS, k=k, algoritmo="merge")
        assert a == b


def test_retrieve_com_contador():
    contador = Contador()
    resultado = retrieve(
        "lista python",
        CHUNKS_PYTHON,
        ESTATISTICAS,
        k=2,
        algoritmo="insertion",
        contador=contador,
    )

    assert len(resultado) == 2
    assert contador.comparacoes > 0


def test_retrieve_ordena_so_candidatos():
    # 3 candidatos ja na ordem certa: 2 comparacoes.
    # Se os 2 chunks de score zero entrassem na ordenacao, seriam 4.
    contador = Contador()
    retrieve("lista python", CHUNKS_PYTHON, ESTATISTICAS, k=2, contador=contador)

    assert contador.comparacoes == 2


def test_retrieve_consulta_vazia():
    assert retrieve("", CHUNKS_PYTHON, ESTATISTICAS, k=5) == []
