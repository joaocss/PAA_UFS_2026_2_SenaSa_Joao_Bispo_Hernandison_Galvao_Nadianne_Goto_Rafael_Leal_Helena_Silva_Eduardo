from dataclasses import dataclass, field


@dataclass
class Estatisticas:
    """Dados do corpus que o tf-idf precisa, calculados uma vez so.

    n_chunks: quantidade de chunks do corpus (N).
    df: para cada termo, em quantos chunks ele aparece.
    """

    n_chunks: int = 0
    df: dict = field(default_factory=dict)
