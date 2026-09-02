"""Baixa o corpus da AV1 na versao fixada e registra os hashes no manifesto.

O script para no download. A extracao das celulas dos notebooks fica com o
preparar_corpus.py, para que ajustes de normalizacao nao obriguem a baixar o
livro de novo.

Uso:
    python scripts/baixar_corpus.py
    python scripts/baixar_corpus.py --forcar        # rebaixa mesmo se ja confere
    python scripts/baixar_corpus.py --destino outra/pasta
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# Versao do corpus usada no trabalho. Trocar este commit muda o snapshot
# inteiro e invalida qualquer execucao anterior.
ORIGEM = "https://github.com/rodrigocarlson/PensePython3ed.git"
COMMIT = "cfde2c450bf4f2ea65326da88e9968f400597e92"

# O recorte sao os capitulos. As pastas brancos e solucoes ficam de fora:
# uma repete o texto sem as respostas, a outra traz gabaritos que nao fazem
# parte do material que queremos indexar.
PASTA_DO_RECORTE = "capitulos"
EXTENSAO = ".ipynb"

RAIZ = Path(__file__).resolve().parents[1]
DESTINO_PADRAO = RAIZ / "data" / "raw"
MANIFESTO_PADRAO = RAIZ / "data" / "corpus_manifest.csv"

COLUNAS = ["tipo", "caminho", "bytes", "sha256", "commit", "url", "acessado_em"]


def impressao_digital(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def hash_do_recorte(arquivos: dict[str, bytes]) -> str:
    """Resume o recorte inteiro em um hash so.

    Concatena caminho e hash de cada arquivo em ordem alfabetica, o que torna o
    resultado independente da ordem de leitura e sensivel a qualquer arquivo
    que entre, saia ou mude.
    """
    resumo = "\n".join(
        f"{caminho}:{impressao_digital(conteudo)}"
        for caminho, conteudo in sorted(arquivos.items())
    )
    return impressao_digital(resumo.encode("utf-8"))


def rodar(comando: list[str], onde: Path) -> None:
    resultado = subprocess.run(comando, cwd=onde, capture_output=True, text=True)
    if resultado.returncode != 0:
        print(" ".join(comando), file=sys.stderr)
        print(resultado.stderr.strip(), file=sys.stderr)
        raise SystemExit(1)


def buscar_do_repositorio(temporaria: Path) -> Path:
    """Traz so o commit fixado, sem o historico inteiro."""
    if shutil.which("git") is None:
        print("git nao encontrado no PATH. Instale o git e tente de novo.", file=sys.stderr)
        raise SystemExit(1)

    print(f"Buscando {ORIGEM} no commit {COMMIT[:7]}")
    rodar(["git", "init", "--quiet"], temporaria)
    rodar(["git", "remote", "add", "origem", ORIGEM], temporaria)
    rodar(["git", "fetch", "--quiet", "--depth", "1", "origem", COMMIT], temporaria)
    rodar(["git", "checkout", "--quiet", "FETCH_HEAD"], temporaria)
    return temporaria


def notebooks_do_recorte(copia: Path) -> dict[str, bytes]:
    """Le apenas os notebooks do recorte, ignorando o resto do repositorio."""
    pasta = copia / PASTA_DO_RECORTE
    encontrados = {
        f"{PASTA_DO_RECORTE}/{arquivo.name}": arquivo.read_bytes()
        for arquivo in sorted(pasta.glob(f"*{EXTENSAO}"))
    }
    if not encontrados:
        print(
            f"Nenhum notebook em {PASTA_DO_RECORTE}/. "
            "A estrutura do repositorio de origem pode ter mudado.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return encontrados


def gravar_notebooks(notebooks: dict[str, bytes], destino: Path) -> None:
    for caminho, conteudo in sorted(notebooks.items()):
        arquivo = destino / caminho
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_bytes(conteudo)


def montar_manifesto(notebooks: dict[str, bytes], acessado_em: str) -> list[dict]:
    base = ORIGEM.removesuffix(".git")
    linhas = [
        {
            "tipo": "arquivo",
            "caminho": caminho,
            "bytes": len(conteudo),
            "sha256": impressao_digital(conteudo),
            "commit": COMMIT,
            "url": f"{base}/blob/{COMMIT}/{caminho}",
            "acessado_em": acessado_em,
        }
        for caminho, conteudo in sorted(notebooks.items())
    ]
    linhas.append(
        {
            "tipo": "agregado",
            "caminho": f"{PASTA_DO_RECORTE}/*{EXTENSAO}",
            "bytes": sum(len(c) for c in notebooks.values()),
            "sha256": hash_do_recorte(notebooks),
            "commit": COMMIT,
            "url": f"{base}/tree/{COMMIT}/{PASTA_DO_RECORTE}",
            "acessado_em": acessado_em,
        }
    )
    return linhas


def ler_manifesto(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def confere_com_manifesto(linhas: list[dict], registrado: list[dict]) -> bool:
    """Compara tudo menos a data de acesso, que muda a cada execucao."""

    def assinatura(registros):
        return [
            (r["tipo"], r["caminho"], str(r["bytes"]), r["sha256"], r["commit"])
            for r in registros
        ]

    return bool(registrado) and assinatura(linhas) == assinatura(registrado)


def gravar_manifesto(linhas: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(linhas)


def ja_esta_em_disco(destino: Path, registrado: list[dict]) -> bool:
    pasta = destino / PASTA_DO_RECORTE
    if not registrado or not pasta.exists():
        return False
    locais = {
        f"{PASTA_DO_RECORTE}/{arquivo.name}": arquivo.read_bytes()
        for arquivo in sorted(pasta.glob(f"*{EXTENSAO}"))
    }
    return bool(locais) and confere_com_manifesto(montar_manifesto(locais, ""), registrado)


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__)
    opcoes.add_argument("--destino", type=Path, default=DESTINO_PADRAO)
    opcoes.add_argument("--manifesto", type=Path, default=MANIFESTO_PADRAO)
    opcoes.add_argument(
        "--forcar",
        action="store_true",
        help="baixa de novo mesmo que o manifesto ja confira",
    )
    args = opcoes.parse_args()

    registrado = ler_manifesto(args.manifesto)
    if not args.forcar and ja_esta_em_disco(args.destino, registrado):
        print(f"Corpus ja esta em {args.destino} e confere com o manifesto.")
        print("Use --forcar para baixar de novo.")
        return 0

    with tempfile.TemporaryDirectory(prefix="corpus-") as area:
        copia = buscar_do_repositorio(Path(area))
        notebooks = notebooks_do_recorte(copia)
        gravar_notebooks(notebooks, args.destino)

    linhas = montar_manifesto(notebooks, date.today().isoformat())
    if confere_com_manifesto(linhas, registrado):
        print("Conteudo identico ao registrado. Manifesto preservado.")
    else:
        gravar_manifesto(linhas, args.manifesto)
        print(f"Manifesto atualizado em {args.manifesto}")

    agregado = linhas[-1]
    print(f"{len(notebooks)} notebooks, {agregado['bytes']} bytes em {args.destino}")
    print(f"Hash do recorte: {agregado['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
