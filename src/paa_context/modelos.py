"""Modelo de dados do chunk e leitura/escrita em JSONL.

Segue o contrato 01 de docs/CONTRATOS.md. Todo modulo que consome chunks
(pontuacao, busca linear, indice, fragmentacao) importa daqui; ninguem
redefine o formato por conta propria.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

TIPOS_VALIDOS = ("markdown", "codigo")


@dataclass(frozen=True)
class Chunk:
    """Um trecho do corpus, ja normalizado, com a origem registrada.

    chunk_id: identificador unico, texto, no formato "<notebook>-c<indice global>".
    source_order: posicao de aparicao no livro, de 0 a n-1, sem repeticao.
        E o criterio de desempate da ordenacao (contrato 02).
    texto: texto normalizado usado na pontuacao.
    tipo: "markdown" ou "codigo".
    arquivo, capitulo, secao, celula_idx: proveniencia.
    token_inicio, token_fim: offsets em tokens dentro da celula (fim exclusivo).
    n_tokens: quantidade de tokens do chunk.
    """

    chunk_id: str
    source_order: int
    texto: str
    tipo: str
    arquivo: str
    capitulo: str
    secao: str
    celula_idx: int
    token_inicio: int
    token_fim: int
    n_tokens: int


CAMPOS_OBRIGATORIOS = tuple(campo.name for campo in fields(Chunk))


class ChunkInvalido(ValueError):
    """Arquivo de chunks fora do contrato 01."""


def _chunk_de_dicionario(registro: dict, linha: int) -> Chunk:
    faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in registro]
    if faltando:
        raise ChunkInvalido(f"linha {linha}: campos ausentes {faltando}")
    extras = [campo for campo in registro if campo not in CAMPOS_OBRIGATORIOS]
    if extras:
        raise ChunkInvalido(f"linha {linha}: campos desconhecidos {extras}")
    if registro["tipo"] not in TIPOS_VALIDOS:
        raise ChunkInvalido(
            f"linha {linha}: tipo {registro['tipo']!r} nao esta em {TIPOS_VALIDOS}"
        )
    for campo in ("source_order", "celula_idx", "token_inicio", "token_fim", "n_tokens"):
        if not isinstance(registro[campo], int) or isinstance(registro[campo], bool):
            raise ChunkInvalido(f"linha {linha}: {campo} precisa ser inteiro")
    if registro["token_fim"] - registro["token_inicio"] != registro["n_tokens"]:
        raise ChunkInvalido(
            f"linha {linha}: token_fim - token_inicio deve ser igual a n_tokens"
        )
    return Chunk(**registro)


def validar_chunks(chunks: list[Chunk]) -> None:
    """Levanta ChunkInvalido se o conjunto viola o contrato 01.

    Regras: chunk_id unico; source_order e exatamente {0, ..., n-1}.
    """
    ids = [c.chunk_id for c in chunks]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        raise ChunkInvalido(f"chunk_id repetido: {repetidos}")
    ordens = sorted(c.source_order for c in chunks)
    if ordens != list(range(len(chunks))):
        raise ChunkInvalido(
            "source_order deve ser exatamente 0..n-1 sem repeticao; "
            f"recebido {ordens[:10]}{'...' if len(ordens) > 10 else ''}"
        )


def carregar_chunks(caminho: Path | str) -> list[Chunk]:
    """Le um JSONL de chunks, valida e devolve a lista em ordem de source_order."""
    caminho = Path(caminho)
    chunks: list[Chunk] = []
    with caminho.open(encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            if not linha.strip():
                continue
            try:
                registro = json.loads(linha)
            except json.JSONDecodeError as erro:
                raise ChunkInvalido(f"linha {numero}: JSON invalido ({erro.msg})") from erro
            chunks.append(_chunk_de_dicionario(registro, numero))
    validar_chunks(chunks)
    chunks.sort(key=lambda c: c.source_order)
    return chunks


def salvar_chunks(chunks: list[Chunk], caminho: Path | str) -> None:
    """Grava a lista em JSONL, um chunk por linha, em ordem de source_order."""
    validar_chunks(chunks)
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        for chunk in sorted(chunks, key=lambda c: c.source_order):
            arquivo.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
