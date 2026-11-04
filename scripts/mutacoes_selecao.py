"""Testes de mutacao da selecao (contrato 14 da AV2).

Quebra o src/paa_context/selecao.py de proposito, uma mudanca por vez, e
conta quantas execucoes de tests/unit/test_selecao.py falham. Se nenhuma
falhar, os testes nao protegem aquele trecho.

Trabalha numa copia temporaria de src/, tests/ e pyproject.toml; o
repositorio nao e alterado, e a copia e apagada no fim.

Uso, a partir da raiz do repositorio:
    python scripts/mutacoes_selecao.py        # as 21 mutacoes
    python scripts/mutacoes_selecao.py 15     # so a mutacao 15
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# corpo atual da DP, da ordenacao ate o fim da reconstrucao
MOCHILA_ATUAL = """    ordenados = sorted(itens, key=lambda item: item.source_order)
    n = len(ordenados)
    peso = W + 1  # maior que o custo de qualquer selecao viavel
    E = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        custo = ordenados[i].custo
        chave = ordenados[i].valor * peso - custo
        linha_seguinte, linha_atual = E[i + 1], E[i]
        for w in range(W + 1):
            linha_atual[w] = linha_seguinte[w]  # sem o item i
            if custo <= w and chave + linha_seguinte[w - custo] > linha_atual[w]:
                linha_atual[w] = chave + linha_seguinte[w - custo]  # com o item i
    escolhidos = []
    w = W
    for i in range(n):
        custo = ordenados[i].custo
        chave = ordenados[i].valor * peso - custo
        if custo <= w and E[i][w] == chave + E[i + 1][w - custo]:
            escolhidos.append(ordenados[i])  # leva-lo ainda alcanca a chave otima
            w -= custo
"""

# a do laboratorio: prefixos por posicao, so valor, "deixa de fora quando empata"
MOCHILA_LABORATORIO = """    ordenados = sorted(itens, key=lambda item: item.posicao)
    n = len(ordenados)
    peso = 1
    D = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        custo, valor = ordenados[i - 1].custo, ordenados[i - 1].valor
        for w in range(W + 1):
            D[i][w] = D[i - 1][w]
            if custo <= w and valor + D[i - 1][w - custo] > D[i][w]:
                D[i][w] = valor + D[i - 1][w - custo]
    escolhidos = []
    w = W
    for i in range(n, 0, -1):
        if D[i][w] != D[i - 1][w]:
            escolhidos.append(ordenados[i - 1])
            w -= ordenados[i - 1].custo
    W = 0  # com peso 1 e W 0, extras["valor_otimo"] = E[0][W] continua valendo
    E = [[D[n][-1]]]
"""

# a versao de 22/10 (regra "leva" por posicao, so valor, sem o desempate por custo)
MOCHILA_22_10 = """    ordenados = sorted(itens, key=lambda item: item.posicao)
    n = len(ordenados)
    peso = 1
    E = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        custo, valor = ordenados[i].custo, ordenados[i].valor
        linha_seguinte, linha_atual = E[i + 1], E[i]
        for w in range(W + 1):
            linha_atual[w] = linha_seguinte[w]
            if custo <= w and valor + linha_seguinte[w - custo] > linha_atual[w]:
                linha_atual[w] = valor + linha_seguinte[w - custo]
    escolhidos = []
    w = W
    for i in range(n):
        custo, valor = ordenados[i].custo, ordenados[i].valor
        if custo <= w and E[i][w] == valor + E[i + 1][w - custo]:
            escolhidos.append(ordenados[i])
            w -= custo
    E = [[E[0][W]]]
    W = 0
"""

# (o que procurar, pelo que trocar, o que a mudanca simula)
MUTACOES = [
    ("chave + linha_seguinte[w - custo] > linha_atual[w]:\n                linha_atual[w] = chave + linha_seguinte[w - custo]",
     "chave + linha_atual[w - custo] > linha_atual[w]:\n                linha_atual[w] = chave + linha_atual[w - custo]",
     "mochila ilimitada: le a linha atual em vez da seguinte (erro do slide 38 da aula 07)"),
    ("if custo <= w and chave + linha_seguinte",
     "if custo < w and chave + linha_seguinte",
     "na tabela, um item que cabe exatamente passa a nao caber"),
    ("if palavras_usadas + item.custo <= W:",
     "if palavras_usadas + item.custo < W:",
     "nos gulosos, um item que enche o orcamento exatamente passa a nao caber"),
    ("if custo <= w and E[i][w] == chave + E[i + 1][w - custo]:",
     "if E[i][w] != E[i + 1][w]:",
     "reconstrucao com a regra antiga 'deixa de fora quando empata'"),
    ("ordenados = sorted(itens, key=lambda item: item.source_order)",
     "ordenados = list(itens)",
     "a DP deixa de ordenar e usa a lista como chega"),
    ("return isinstance(numero, int) and not isinstance(numero, bool)",
     "return isinstance(numero, int)",
     "a validacao passa a aceitar True e False como numeros"),
    ("if not _inteiro(item.valor) or item.valor < 1:",
     "if not _inteiro(item.valor) or item.valor < 0:",
     "a validacao passa a aceitar valor 0"),
    ("_guloso(itens, W, lambda item: (-item.valor, item.posicao), \"guloso_valor\")",
     "_guloso(itens, W, lambda item: (-item.valor,), \"guloso_valor\")",
     "S2 deixa de desempatar pela posicao e passa a usar a ordem da lista"),
    ("-Fraction(item.valor, item.custo)",
     "-(item.valor / item.custo)",
     "S3 compara densidades em float em vez de fracao exata"),
    ("valor = round(escore * ESCALA_VALOR)",
     "valor = int(escore * ESCALA_VALOR)",
     "a conversao trunca o escore em vez de arredondar"),
    ("if maior_isolado.valor > selecao_gulosa.valor_total:",
     "if False:",
     "S4 vira S3: nunca usa o item isolado (perde a garantia de metade)"),
    ("    for item in itens:\n        if not _inteiro(item.custo)",
     "    for item in itens[:1]:\n        if not _inteiro(item.custo)",
     "a validacao so olha o primeiro item da lista"),
    (MOCHILA_ATUAL,
     MOCHILA_LABORATORIO,
     "a DP inteira do laboratorio (tabela de prefixos, reconstrucao de baixo para cima)"),
    (MOCHILA_ATUAL,
     MOCHILA_22_10,
     "a DP de 22/10: regra 'leva' por posicao, sem desempate por custo nem source_order"),
    ("peso = W + 1  # maior que o custo de qualquer selecao viavel",
     "peso = W + 1\n    peso = 1",
     "a DP perde o desempate por menor custo (chave = valor - custo)"),
    ("ordenados = sorted(itens, key=lambda item: item.source_order)",
     "ordenados = sorted(itens, key=lambda item: item.posicao)",
     "a DP desempata pela posicao no ranking, e nao pelo source_order"),
    ("(-Fraction(item.valor, item.custo), -item.valor, item.source_order)",
     "(-Fraction(item.valor, item.custo), item.source_order)",
     "S3 deixa de preferir o maior valor no empate da razao"),
    ("(-Fraction(item.valor, item.custo), -item.valor, item.source_order)",
     "(-Fraction(item.valor, item.custo), -item.valor, item.posicao)",
     "S3 desempata pela posicao, e nao pelo source_order"),
    ("            raise ValueError(f\"chunk_id {chunk.chunk_id!r} repetido nos resultados\")",
     "            continue",
     "a conversao volta a descartar o chunk_id repetido em silencio"),
    ("        if escore == 0:\n            continue",
     "        if escore == 0:\n            pass",
     "a conversao deixa passar escore zero"),
    ("extras={\"valor_otimo\": (E[0][W] + W) // peso}",
     "extras={\"valor_otimo\": E[0][W] // peso}",
     "valor otimo lido da chave sem compensar o custo"),
]


def rodar(pasta):
    saida = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-rf", "tests/unit/test_selecao.py"],
        cwd=pasta, capture_output=True, text=True,
    ).stdout
    resumo = saida.strip().splitlines()[-1] if saida.strip() else "(sem saida)"
    funcoes = sorted({linha.split("::")[1].split("[")[0].split(" ")[0]
                      for linha in saida.splitlines() if linha.startswith("FAILED")})
    return resumo, funcoes


def main():
    escolhidas = [int(a) for a in sys.argv[1:]] or range(1, len(MUTACOES) + 1)
    with tempfile.TemporaryDirectory(prefix="mutacoes_selecao_") as tmp:
        pasta = Path(tmp)
        shutil.copytree(REPO / "src", pasta / "src")
        shutil.copytree(REPO / "tests", pasta / "tests")
        shutil.copy(REPO / "pyproject.toml", pasta / "pyproject.toml")
        alvo = pasta / "src" / "paa_context" / "selecao.py"
        original = alvo.read_text(encoding="utf-8")

        resumo, _ = rodar(pasta)
        print(f"Sem mutacao: {resumo}\n")
        for numero in escolhidas:
            procurar, trocar, descricao = MUTACOES[numero - 1]
            if original.count(procurar) != 1:
                print(f"Mutacao {numero}: trecho nao encontrado; o selecao.py mudou?\n")
                continue
            alvo.write_text(original.replace(procurar, trocar), encoding="utf-8")
            resumo, funcoes = rodar(pasta)
            print(f"Mutacao {numero}: {descricao}")
            print(f"  resultado: {resumo}")
            for funcao in funcoes:
                print(f"    - {funcao}")
            print()
            alvo.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    main()
