import os
import re
import pandas as pd

RESULTS_DIR = "results"
OUTPUT_FILE = "clean_results.csv"

def extract_metadata(filename):
    # exemplo: image_200kb_700_inst2_stats.csv
    match = re.match(r"(.*?)_(\d+)_inst(\d+)_stats\.csv", filename)
    if not match:
        return None

    scenario, users, instances = match.groups()
    return {
        "scenario": scenario,
        "users": int(users),
        "instances": int(instances),
    }


def process_file(filepath):
    df = pd.read_csv(filepath)

    # linha "Aggregated"
    df = df[df["Name"] == "Aggregated"]

    if df.empty:
        return None

    row = df.iloc[0]

    requests = row["Request Count"]
    failures = row["Failure Count"]

    failure_rate = failures / requests if requests > 0 else 0

    return {
        "requests": requests,
        "failures": failures,
        "failure_rate": failure_rate,
        "avg_response_time": row["Average Response Time"],
        "p95": row["95%"],
    }


def main():
    records = []

    for file in os.listdir(RESULTS_DIR):
        if not file.endswith("_stats.csv"):
            continue

        metadata = extract_metadata(file)
        if not metadata:
            continue

        filepath = os.path.join(RESULTS_DIR, file)
        metrics = process_file(filepath)

        if metrics:
            record = {**metadata, **metrics}
            records.append(record)

    df_final = pd.DataFrame(records)

    # ordenação para análise
    df_final = df_final.sort_values(
        by=["scenario", "instances", "users"]
    )

    df_final.to_csv(OUTPUT_FILE, index=False)
    print(f"Arquivo gerado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()