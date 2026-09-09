from dataclasses import dataclass


@dataclass
class Contador:
    """Contadores para analise experimental e modelo RAM.

    comparacoes: cada comparacao entre scores (ou chaves) de dois itens.
    trocas: no Insertion Sort, cada deslocamento de um item para a direita;
            no Merge Sort, cada copia de um item para a lista de saida do merge.
    """

    comparacoes: int = 0
    trocas: int = 0
