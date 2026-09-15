import json
from dataclasses import asdict

import pytest

from paa_context.fragmentacao import (
    Celula,
    extrair_celulas,
    fragmentar,
    normalizar_texto,
    tokenizar,
)
from paa_context.modelos import carregar_chunks, salvar_chunks


def celula(conteudo, tipo="markdown", indice=0, secao=""):
    return Celula("capitulos/chap05.ipynb", "Condicionais e Recursão", secao, indice, tipo, conteudo)


def texto_com(n_palavras):
    return " ".join(f"p{i}" for i in range(n_palavras))


def test_normalizacao_mantem_acento():
    assert normalizar_texto("Função") == "função"


def test_normalizacao_compacta_espacos_e_remove_invisiveis():
    assert normalizar_texto("Variáveis ​​e   Instruções") == "variáveis e instruções"


def test_tokenizar_separa_pontuacao():
    assert tokenizar("a,b. c") == ["a", "b", "c"]


def test_celula_grande_vira_varios_chunks():
    # Passo de 224 tokens: janelas [0,256), [224,480) e [448,700).
    # O SEMANA1.md falava em 4 chunks; a conta certa da 3.
    chunks = fragmentar([celula(texto_com(700))], tamanho=256, sobreposicao=32)
    assert [(c.token_inicio, c.token_fim) for c in chunks] == [(0, 256), (224, 480), (448, 700)]
    assert chunks[0].n_tokens == 256


def test_celula_pequena_vira_um_chunk():
    chunks = fragmentar([celula(texto_com(100))])
    assert len(chunks) == 1
    assert chunks[0].n_tokens == 100


def test_codigo_e_markdown_nunca_dividem_chunk():
    chunks = fragmentar([celula("x = 1", tipo="codigo", indice=3), celula("texto solto", indice=4)])
    assert [c.tipo for c in chunks] == ["codigo", "markdown"]


def test_ids_unicos_e_source_order_contiguo():
    chunks = fragmentar([celula(texto_com(600), indice=i) for i in range(5)])
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
    assert [c.source_order for c in chunks] == list(range(len(chunks)))


def test_fragmentar_e_deterministico():
    celulas = [celula(texto_com(300)), celula("print(1)", tipo="codigo", indice=1)]
    assert fragmentar(celulas) == fragmentar(celulas)


def test_sobreposicao_invalida():
    with pytest.raises(ValueError):
        fragmentar([celula("a b c")], tamanho=10, sobreposicao=10)


def test_salvar_e_carregar_dao_a_volta(tmp_path):
    chunks = fragmentar([celula(texto_com(300)), celula("print(1)", tipo="codigo", indice=1)])
    caminho = tmp_path / "chunks.jsonl"
    salvar_chunks(chunks, caminho)
    assert carregar_chunks(caminho) == chunks


def test_carregar_rejeita_source_order_com_furo(tmp_path):
    # Grava o arquivo a mao: salvar_chunks ja recusaria uma lista com furo.
    chunks = fragmentar([celula(texto_com(300))])
    registros = [asdict(chunks[0]), {**asdict(chunks[1]), "source_order": 7}]
    caminho = tmp_path / "chunks.jsonl"
    caminho.write_text("".join(json.dumps(r) + "\n" for r in registros), encoding="utf-8")
    with pytest.raises(ValueError):
        carregar_chunks(caminho)


def test_extrair_celulas_descarta_cabecalho_e_acompanha_titulos(tmp_path):
    notebook = {
        "cells": [
            {"cell_type": "markdown", "source": ["Você pode adquirir versões impressas..."]},
            {"cell_type": "code", "source": ["def download(url):\n", "    pass"], "outputs": [{"text": "lixo"}]},
            {"cell_type": "markdown", "source": ["# Condicionais e Recursão\n", "\n", "O tópico principal..."]},
            {"cell_type": "code", "source": ["minutes = 105"]},
            {"cell_type": "markdown", "source": ["## Recursão\n", "É legal uma função chamar a si mesma."]},
            {"cell_type": "raw", "source": ["ignorado"]},
            {"cell_type": "code", "source": [""]},
        ]
    }
    caminho = tmp_path / "chap05.ipynb"
    caminho.write_text(json.dumps(notebook), encoding="utf-8")

    celulas = extrair_celulas(caminho)

    assert [c.indice for c in celulas] == [2, 3, 4]
    assert [c.tipo for c in celulas] == ["markdown", "codigo", "markdown"]
    assert celulas[0].capitulo == "Condicionais e Recursão" and celulas[0].secao == ""
    assert celulas[1].secao == ""
    assert celulas[2].secao == "Recursão"
    assert celulas[0].arquivo == "chap05.ipynb"
