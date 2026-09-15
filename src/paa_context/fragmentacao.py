"""Ingestao dos notebooks e corte em chunks.

Le os .ipynb do corpus, descarta saidas e metadados, acompanha o ultimo
titulo para preencher capitulo e secao, e corta cada celula em janelas de
`tamanho` tokens com `sobreposicao` tokens repetidos entre janelas vizinhas.
Celula de texto e celula de codigo nunca dividem o mesmo chunk.

Token aqui e uma palavra apos a normalizacao: sequencia de letras, digitos
ou sublinhado, com acento preservado. O mesmo criterio vale para a consulta.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

# O formato do chunk (contrato 01) e a leitura/escrita em JSONL ficam em modelos.py.
from .modelos import Chunk

PALAVRA = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class Celula:
    arquivo: str
    capitulo: str
    secao: str
    indice: int
    tipo: str        # "markdown" ou "codigo"
    conteudo: str


def _sem_invisiveis(texto: str) -> str:
    # O livro traz alguns espacos de largura zero (U+200B) colados em titulos.
    return "".join(c for c in texto if unicodedata.category(c) != "Cf")


def normalizar_texto(texto: str) -> str:
    """Minusculas, NFKC e espacos compactados. Acentos ficam."""
    texto = unicodedata.normalize("NFKC", _sem_invisiveis(texto)).lower()
    return " ".join(texto.split())


def tokenizar(texto: str) -> list[str]:
    return PALAVRA.findall(normalizar_texto(texto))


def _titulo(linha: str) -> tuple[int, str] | None:
    """Devolve (nivel, texto) se a linha for um titulo markdown."""
    m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", _sem_invisiveis(linha).strip())
    if not m:
        return None
    return len(m.group(1)), m.group(2).strip()


def extrair_celulas(caminho_notebook: Path, raiz: Path | None = None) -> list[Celula]:
    """Le um notebook e devolve as celulas de texto e codigo, em ordem.

    Celulas anteriores ao primeiro titulo de nivel 1 sao descartadas: nos
    notebooks do Pense Python elas trazem o link de compra e o helper de
    download, que nao fazem parte do capitulo.
    """
    with open(caminho_notebook, encoding="utf-8") as arquivo:
        notebook = json.load(arquivo)

    nome = str(caminho_notebook.relative_to(raiz)) if raiz else caminho_notebook.name
    capitulo = ""
    secao = ""
    celulas: list[Celula] = []

    for indice, celula in enumerate(notebook.get("cells", [])):
        tipo_bruto = celula.get("cell_type")
        if tipo_bruto not in ("markdown", "code"):
            continue
        fonte = celula.get("source", "")
        conteudo = "".join(fonte) if isinstance(fonte, list) else fonte
        if not conteudo.strip():
            continue

        if tipo_bruto == "markdown":
            for linha in conteudo.splitlines():
                t = _titulo(linha)
                if t is None:
                    continue
                nivel, texto = t
                if nivel == 1:
                    capitulo, secao = texto, ""
                else:
                    secao = texto
            tipo = "markdown"
        else:
            tipo = "codigo"

        if not capitulo:
            continue

        celulas.append(Celula(nome, capitulo, secao, indice, tipo, conteudo))

    return celulas


def _janelas(n_tokens: int, tamanho: int, sobreposicao: int) -> list[tuple[int, int]]:
    """Intervalos [inicio, fim) que cobrem 0..n_tokens com sobreposicao."""
    if n_tokens <= tamanho:
        return [(0, n_tokens)]
    passo = tamanho - sobreposicao
    intervalos = []
    inicio = 0
    while True:
        fim = min(inicio + tamanho, n_tokens)
        intervalos.append((inicio, fim))
        if fim == n_tokens:
            return intervalos
        inicio += passo


def fragmentar(celulas: list[Celula], tamanho: int = 256, sobreposicao: int = 32) -> list[Chunk]:
    if tamanho <= 0 or sobreposicao < 0 or sobreposicao >= tamanho:
        raise ValueError("tamanho deve ser positivo e a sobreposicao menor que ele")

    chunks: list[Chunk] = []
    for celula in celulas:
        tokens = tokenizar(celula.conteudo)
        if not tokens:
            continue
        prefixo = Path(celula.arquivo).stem
        for inicio, fim in _janelas(len(tokens), tamanho, sobreposicao):
            ordem = len(chunks)
            chunks.append(Chunk(
                chunk_id=f"{prefixo}-c{ordem:04d}",
                source_order=ordem,
                texto=" ".join(tokens[inicio:fim]),
                tipo=celula.tipo,
                arquivo=celula.arquivo,
                capitulo=celula.capitulo,
                secao=celula.secao,
                celula_idx=celula.indice,
                token_inicio=inicio,
                token_fim=fim,
                n_tokens=fim - inicio,
            ))
    return chunks
