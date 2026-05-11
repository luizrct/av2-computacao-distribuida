from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_FILE = Path("results/processed/final_results.csv")
OUTPUT_DIR = Path("results/graphs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_FILE)


SCENARIO_LABELS = {
    ("python", "cache"): "Python com cache",
    ("python", "no_cache"): "Python sem cache",
    ("ruby", "cache"): "Ruby com cache",
    ("ruby", "no_cache"): "Ruby sem cache",
}


METRICS = {
    "avg_response_time": "Tempo médio de resposta (ms)",
    "median_response_time": "Mediana do tempo de resposta (ms)",
    "p95_response_time": "Percentil 95 do tempo de resposta (ms)",
    "p99_response_time": "Percentil 99 do tempo de resposta (ms)",
    "requests_per_second": "Requisições por segundo",
    "failure_rate": "Taxa de falha (%)",
}


for metric, ylabel in METRICS.items():
    plt.figure(figsize=(10, 6))

    for (language, cache_mode), group in df.groupby(["language", "cache_mode"]):
        group = group.sort_values("users")

        label = SCENARIO_LABELS.get(
            (language, cache_mode),
            f"{language} {cache_mode}"
        )

        plt.plot(
            group["users"],
            group[metric],
            marker="o",
            label=label,
        )

    plt.title(ylabel)
    plt.xlabel("Quantidade de usuários virtuais")
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output_file = OUTPUT_DIR / f"{metric}.png"
    plt.savefig(output_file, dpi=300)
    plt.close()

    print(f"Gráfico gerado: {output_file}")