"""Testes do contrato 01: formato do chunk, validacao e leitura/escrita."""

import json
from pathlib import Path

import pytest

from paa_context.modelos import (
    CAMPOS_OBRIGATORIOS,
    Chunk,
    ChunkInvalido,
    carregar_chunks,
    salvar_chunks,
    validar_chunks,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
CHUNKS_SINTETICOS = FIXTURES / "chunks_sinteticos.jsonl"


def chunk_exemplo(**alteracoes) -> Chunk:
    base = dict(
        chunk_id="x-c0000", source_order=0, texto="um dois tres", tipo="markdown",
        arquivo="fixtures/x.ipynb", capitulo="X", secao="", celula_idx=0,
        token_inicio=0, token_fim=3, n_tokens=3,
    )
    base.update(alteracoes)
    return Chunk(**base)


def test_fixture_carrega_vinte_chunks_em_ordem():
    chunks = carregar_chunks(CHUNKS_SINTETICOS)
    assert len(chunks) == 20
    assert [c.source_order for c in chunks] == list(range(20))


def test_fixture_tem_os_onze_campos_e_nada_mais():
    primeira_linha = CHUNKS_SINTETICOS.read_text(encoding="utf-8").splitlines()[0]
    assert set(json.loads(primeira_linha)) == set(CAMPOS_OBRIGATORIOS)
    assert len(CAMPOS_OBRIGATORIOS) == 11


def test_fixture_tem_texto_e_codigo():
    tipos = {c.tipo for c in carregar_chunks(CHUNKS_SINTETICOS)}
    assert tipos == {"markdown", "codigo"}


def test_fixture_ordem_alfabetica_dos_ids_difere_da_source_order():
    # Garante que um teste de desempate por source_order nao passa por acaso
    # se alguem ordenar por chunk_id.
    chunks = carregar_chunks(CHUNKS_SINTETICOS)
    por_id = [c.chunk_id for c in sorted(chunks, key=lambda c: c.chunk_id)]
    por_ordem = [c.chunk_id for c in chunks]
    assert por_id != por_ordem


def test_chunk_id_repetido_e_rejeitado():
    with pytest.raises(ChunkInvalido, match="repetido"):
        validar_chunks([chunk_exemplo(), chunk_exemplo(source_order=1)])


def test_source_order_com_buraco_e_rejeitado():
    with pytest.raises(ChunkInvalido, match="source_order"):
        validar_chunks([chunk_exemplo(), chunk_exemplo(chunk_id="x-c0002", source_order=2)])


def test_source_order_repetido_e_rejeitado():
    with pytest.raises(ChunkInvalido, match="source_order"):
        validar_chunks([chunk_exemplo(), chunk_exemplo(chunk_id="x-c0001")])


def test_tipo_desconhecido_e_rejeitado(tmp_path):
    caminho = tmp_path / "ruim.jsonl"
    registro = {**vars(chunk_exemplo()), "tipo": "html"}
    caminho.write_text(json.dumps(registro) + "\n", encoding="utf-8")
    with pytest.raises(ChunkInvalido, match="tipo"):
        carregar_chunks(caminho)


def test_campo_ausente_e_rejeitado(tmp_path):
    caminho = tmp_path / "ruim.jsonl"
    registro = vars(chunk_exemplo())
    del registro["secao"]
    caminho.write_text(json.dumps(registro) + "\n", encoding="utf-8")
    with pytest.raises(ChunkInvalido, match="ausentes"):
        carregar_chunks(caminho)


def test_n_tokens_inconsistente_e_rejeitado(tmp_path):
    caminho = tmp_path / "ruim.jsonl"
    registro = {**vars(chunk_exemplo()), "n_tokens": 99}
    caminho.write_text(json.dumps(registro) + "\n", encoding="utf-8")
    with pytest.raises(ChunkInvalido, match="n_tokens"):
        carregar_chunks(caminho)


def test_salvar_e_carregar_preserva_tudo(tmp_path):
    originais = carregar_chunks(CHUNKS_SINTETICOS)
    caminho = tmp_path / "copia.jsonl"
    salvar_chunks(list(reversed(originais)), caminho)
    assert carregar_chunks(caminho) == originais


def test_chunk_e_imutavel():
    with pytest.raises(Exception):
        chunk_exemplo().texto = "outro"  # type: ignore[misc]
