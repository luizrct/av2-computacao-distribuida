from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_FILE = Path("results/processed/final_results.csv")
OUTPUT_DIR = Path("results/graphs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_FILE)


METRICS = {
    "p95_response_time": "Percentil 95 do tempo de resposta (ms)",
    "failure_rate": "Taxa de falha (%)",
}


CACHE_LABELS = {
    "no_cache": "Sem cache",
    "cache": "Com cache",
}


LANGUAGE_LABELS = {
    "python": "Python",
    "ruby": "Ruby",
}


LANGUAGE_COLORS = {
    "python": ["#93C5FD", "#2563EB"],  # azul claro / azul forte
    "ruby": ["#FCA5A5", "#DC2626"],    # vermelho claro / vermelho forte
}


for language in ["python", "ruby"]:
    language_df = df[df["language"] == language].copy()

    for metric, ylabel in METRICS.items():
        pivot_df = language_df.pivot_table(
            index="users",
            columns="cache_mode",
            values=metric,
            aggfunc="mean",
        ).sort_index()

        pivot_df = pivot_df.rename(columns=CACHE_LABELS)

        colors = LANGUAGE_COLORS[language]

        ax = pivot_df.plot(
            kind="bar",
            figsize=(10, 6),
            width=0.8,
            color=colors,
        )

        title = f"{LANGUAGE_LABELS[language]} - {ylabel}"

        ax.set_title(title)
        ax.set_xlabel("Quantidade de usuários virtuais")
        ax.set_ylabel(ylabel)
        ax.set_yscale("log")
        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.5,
        )

        ax.legend(title="Cenário")

        plt.xticks(rotation=0)
        plt.tight_layout()

        output_file = OUTPUT_DIR / f"{language}_{metric}.png"

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight",
        )

        plt.close()

        print(f"Gráfico gerado: {output_file}")