import os
import re
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
OUTPUT_DIR = "graphs"

SCENARIO_LABELS = {
    "image_1mb": "Post com imagem ~1MB",
    "text_400kb": "Post com texto ~400KB",
    "image_300kb": "Post com imagem ~300KB",
    "all": "Todos os cenários",
}

FILENAME_PATTERN = re.compile(
    r"(?P<scenario>image_1mb|text_400kb|image_300kb|all)_(?P<users>\d+)_inst(?P<instances>\d+)_stats\.csv"
)


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def read_metrics_from_csv(file_path):
    df = pd.read_csv(file_path)

    row = df[df["Name"] == "Aggregated"]

    if row.empty:
        row = df.iloc[[-1]]

    p95_ms = float(row["95%"].values[0])
    request_count = int(row["Request Count"].values[0])
    failure_count = int(row["Failure Count"].values[0])

    failure_percentage = 0
    if request_count > 0:
        failure_percentage = (failure_count / request_count) * 100

    return p95_ms / 1000, failure_percentage


def load_results():
    data = []

    for filename in os.listdir(RESULTS_DIR):
        match = FILENAME_PATTERN.match(filename)

        if not match:
            continue

        scenario = match.group("scenario")
        users = int(match.group("users"))
        instances = int(match.group("instances"))

        file_path = os.path.join(RESULTS_DIR, filename)
        p95_seconds, failure_percentage = read_metrics_from_csv(file_path)

        data.append({
            "scenario": scenario,
            "users": users,
            "instances": instances,
            "p95_seconds": p95_seconds,
            "failure_percentage": failure_percentage,
        })

    return pd.DataFrame(data)


def plot_by_users(df, scenario, metric_column, ylabel, suffix):
    scenario_df = df[df["scenario"] == scenario]

    users = sorted(scenario_df["users"].unique())
    instances = sorted(scenario_df["instances"].unique())

    x = range(len(users))
    bar_width = 0.8 / len(instances)

    plt.figure(figsize=(9, 5))

    for i, inst in enumerate(instances):
        values = []

        for user_count in users:
            row = scenario_df[
                (scenario_df["users"] == user_count) &
                (scenario_df["instances"] == inst)
            ]

            values.append(0 if row.empty else row[metric_column].values[0])

        positions = [
            pos + (i - (len(instances) - 1) / 2) * bar_width
            for pos in x
        ]

        plt.bar(
            positions,
            values,
            width=bar_width,
            label=f"{inst} instância" if inst == 1 else f"{inst} instâncias"
        )

    plt.xlabel("Número de usuários")
    plt.ylabel(ylabel)
    plt.title(SCENARIO_LABELS.get(scenario, scenario))
    plt.xticks(list(x), users)
    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(OUTPUT_DIR, f"{scenario}_{suffix}_por_usuarios.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Gráfico salvo: {output_path}")


def plot_by_instances(df, scenario, metric_column, ylabel, suffix):
    scenario_df = df[df["scenario"] == scenario]

    users = sorted(scenario_df["users"].unique())
    instances = sorted(scenario_df["instances"].unique())

    x = range(len(instances))
    bar_width = 0.8 / len(users)

    plt.figure(figsize=(9, 5))

    for i, user_count in enumerate(users):
        values = []

        for inst in instances:
            row = scenario_df[
                (scenario_df["users"] == user_count) &
                (scenario_df["instances"] == inst)
            ]

            values.append(0 if row.empty else row[metric_column].values[0])

        positions = [
            pos + (i - (len(users) - 1) / 2) * bar_width
            for pos in x
        ]

        plt.bar(
            positions,
            values,
            width=bar_width,
            label=f"{user_count} usuários"
        )

    plt.xlabel("Número de instâncias")
    plt.ylabel(ylabel)
    plt.title(SCENARIO_LABELS.get(scenario, scenario))
    plt.xticks(list(x), instances)
    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(OUTPUT_DIR, f"{scenario}_{suffix}_por_instancias.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Gráfico salvo: {output_path}")


def main():
    ensure_output_dir()

    df = load_results()

    if df.empty:
        raise ValueError("Nenhum arquivo *_stats.csv válido foi encontrado.")

    for scenario in sorted(df["scenario"].unique()):
        plot_by_users(
            df,
            scenario,
            metric_column="p95_seconds",
            ylabel="Tempo de resposta (s)",
            suffix="p95",
        )

        plot_by_users(
            df,
            scenario,
            metric_column="failure_percentage",
            ylabel="Falhas de requests (%)",
            suffix="falhas",
        )

        plot_by_instances(
            df,
            scenario,
            metric_column="p95_seconds",
            ylabel="Tempo de resposta (s)",
            suffix="p95",
        )

        plot_by_instances(
            df,
            scenario,
            metric_column="failure_percentage",
            ylabel="Falhas de requests (%)",
            suffix="falhas",
        )


if __name__ == "__main__":
    main()