"""Busca binaria no vocabulario ordenado do indice invertido (configuracao C2).

Conta toda comparacao entre strings no contador, como fazem as ordenacoes.
E o que a analise usa para a recorrencia T(V) = T(V/2) + Theta(1).
"""

from .contador import Contador


def busca_binaria(vocabulario, termo, contador=None):
    """Posicao de `termo` em `vocabulario`, ou -1 se nao estiver.

    Pre-condicao: vocabulario ordenado pela ordem natural das strings,
    a mesma usada nas comparacoes abaixo.

    Invariante: se o termo esta no vocabulario, esta em vocabulario[lo:hi].
    hi - lo cai a cada volta, entao o laco termina.

    Tempo: O(log V) comparacoes no pior caso; melhor caso uma comparacao.
    Espaco extra: O(1).
    """
    if contador is None:
        contador = Contador()

    lo, hi = 0, len(vocabulario)
    while lo < hi:
        meio = (lo + hi) // 2
        contador.comparacoes += 1
        if vocabulario[meio] == termo:
            return meio
        contador.comparacoes += 1
        if vocabulario[meio] < termo:
            lo = meio + 1
        else:
            hi = meio
    return -1
