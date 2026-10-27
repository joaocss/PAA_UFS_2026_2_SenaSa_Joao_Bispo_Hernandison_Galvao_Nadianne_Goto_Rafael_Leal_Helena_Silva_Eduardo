
from pathlib import Path
import math
import matplotlib.pyplot as plt

# Comparações observadas na execução do Merge Sort.
p = [10, 30, 50, 100, 200]
comparacoes = [23, 112, 232, 559, 1296]

# Função de referência assintótica.
referencia = [x * math.log2(x) for x in p]

saida = Path(__file__).resolve().parent / "resultados"
saida.mkdir(parents=True, exist_ok=True)

plt.figure(figsize=(8, 5))

plt.plot(
    p, comparacoes,
    marker="o",
    label="Comparações observadas"
)

plt.plot(
    p, referencia,
    marker="s",
    linestyle="--",
    label=r"Referência $P\log_2 P$"
)

plt.xlabel("Quantidade de candidatos (P)")
plt.ylabel("Número de comparações")
plt.title("Crescimento das comparações do Merge Sort — C3")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

arquivo = saida / "comparacoes_merge_sort.png"
plt.savefig(arquivo, dpi=200)
plt.close()

print(f"Gráfico gerado: {arquivo}")
