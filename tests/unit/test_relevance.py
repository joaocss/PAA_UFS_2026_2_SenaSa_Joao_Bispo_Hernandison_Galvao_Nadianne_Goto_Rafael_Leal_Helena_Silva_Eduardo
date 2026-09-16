import math
from dataclasses import replace

from paa_context.linear_search import CHUNKS_PYTHON
from paa_context.relevance import build_statistics, relevance_score

# Nos 5 chunks de CHUNKS_PYTHON, "lista" aparece em 1, "python" em 3 e "uma" em 2.
ESTATISTICAS = build_statistics(CHUNKS_PYTHON)
IDF_LISTA = math.log(6 / 2) + 1
IDF_PYTHON = math.log(6 / 4) + 1


def test_estatisticas():
    assert ESTATISTICAS.n_chunks == 5
    assert ESTATISTICAS.df["lista"] == 1
    assert ESTATISTICAS.df["python"] == 3


def test_df_conta_chunks_e_nao_ocorrencias():
    # "uma" aparece duas vezes no chunk 0 e duas no chunk 1
    assert ESTATISTICAS.df["uma"] == 2


def test_relevancia_total():
    query = "lista python"
    chunk = CHUNKS_PYTHON[0]

    assert relevance_score(query, chunk, ESTATISTICAS) == IDF_LISTA + IDF_PYTHON


def test_relevancia_parcial():
    query = "lista python funcao"
    chunk = CHUNKS_PYTHON[0]

    assert relevance_score(query, chunk, ESTATISTICAS) == IDF_LISTA + IDF_PYTHON


def test_sem_relevancia():
    query = "lista python"
    chunk = CHUNKS_PYTHON[4]

    assert relevance_score(query, chunk, ESTATISTICAS) == 0.0


def test_query_vazia():
    assert relevance_score("", CHUNKS_PYTHON[0], ESTATISTICAS) == 0.0


def test_termos_repetidos():
    query = "lista lista lista python"
    chunk = replace(CHUNKS_PYTHON[0], texto="Uma lista em Python.")

    assert relevance_score(query, chunk, ESTATISTICAS) == 3 * IDF_LISTA + IDF_PYTHON


def test_termo_repetido_no_chunk():
    # "uma" ocorre 2 vezes no chunk 0: tf = 1 + ln 2
    query = "uma"
    chunk = CHUNKS_PYTHON[0]

    assert relevance_score(query, chunk, ESTATISTICAS) == (1 + math.log(2)) * (math.log(6 / 3) + 1)


def test_remove_acentos():
    chunk = replace(CHUNKS_PYTHON[0], texto="Recursão é útil.")
    estatisticas = build_statistics([chunk])

    assert relevance_score("recursão", chunk, estatisticas) > 0
    assert relevance_score("recursão", chunk, estatisticas) == relevance_score("recursao", chunk, estatisticas)
