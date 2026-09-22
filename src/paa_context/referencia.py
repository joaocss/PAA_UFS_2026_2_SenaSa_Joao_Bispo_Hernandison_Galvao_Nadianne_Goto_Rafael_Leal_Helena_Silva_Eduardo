"""C4: baseline de referencia com o TF-IDF do scikit-learn.

Fica separado de C1, C2 e C3 de proposito: aqui a pontuacao, a busca e a
ordenacao sao da biblioteca, nao da equipe. Serve para comparar a lista da
equipe com a de uma implementacao de mercado, nao entra na equivalencia H1.

Mesmo pre-processamento (normalize) e mesma familia de formula do contrato 02
(sublinear_tf: tf = 1 + ln f; smooth_idf: idf = ln((N+1)/(df+1)) + 1). A
diferenca e a normalizacao L2 dos vetores: o escore vira cosseno, o que
favorece chunks curtos em relacao a soma sem normalizacao da equipe.

Empates sao desfeitos por source_order, como nas outras configuracoes.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .preprocessing import normalize


@dataclass
class IndiceReferencia:
    chunks: list
    vetorizador: TfidfVectorizer
    matriz: object  # scipy.sparse, uma linha por chunk, ja normalizada em L2
    ordens: np.ndarray


def construir_referencia(chunks):
    """Ajusta o TfidfVectorizer aos chunks. Custo da biblioteca, fora do modelo RAM da equipe."""
    vetorizador = TfidfVectorizer(
        tokenizer=normalize,
        preprocessor=None,
        lowercase=False,
        token_pattern=None,
        sublinear_tf=True,
        smooth_idf=True,
        norm="l2",
    )
    matriz = vetorizador.fit_transform([chunk.texto for chunk in chunks])
    ordens = np.array([chunk.source_order for chunk in chunks])
    return IndiceReferencia(chunks=list(chunks), vetorizador=vetorizador, matriz=matriz, ordens=ordens)


def recuperar_referencia(consulta, referencia, k):
    """Devolve (top-k como lista de (chunk, escore), numero de candidatos com escore > 0)."""
    if k <= 0:
        return [], 0

    vetor = referencia.vetorizador.transform([consulta])
    escores = (referencia.matriz @ vetor.T).toarray().ravel()

    candidatos = np.flatnonzero(escores > 0)
    # lexsort usa a ultima chave como principal: maior escore, depois menor source_order.
    ordem = candidatos[np.lexsort((referencia.ordens[candidatos], -escores[candidatos]))]

    resultados = [(referencia.chunks[i], float(escores[i])) for i in ordem[:k]]
    return resultados, len(candidatos)
