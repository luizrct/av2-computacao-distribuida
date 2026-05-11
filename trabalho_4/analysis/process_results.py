import re
from pathlib import Path

import pandas as pd


RAW_DIR = Path("results/raw")
PROCESSED_DIR = Path("results/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_DIR / "final_results.csv"


def parse_filename(filename: str):
    pattern = r"(python|ruby)_(cache|no_cache)_(\d+)_users_stats\.csv"
    match = re.match(pattern, filename)

    if not match:
        return None

    language = match.group(1)
    cache_mode = match.group(2)
    users = int(match.group(3))

    return language, cache_mode, users


rows = []

for file_path in RAW_DIR.glob("*_stats.csv"):
    parsed = parse_filename(file_path.name)

    if not parsed:
        continue

    language, cache_mode, users = parsed

    df = pd.read_csv(file_path)

    aggregated = df[df["Name"] == "Aggregated"]

    if aggregated.empty:
        continue

    row = aggregated.iloc[0]

    request_count = row["Request Count"]
    failure_count = row["Failure Count"]

    failure_rate = 0

    if request_count > 0:
        failure_rate = (failure_count / request_count) * 100

    rows.append({
        "language": language,
        "cache_mode": cache_mode,
        "users": users,
        "request_count": request_count,
        "failure_count": failure_count,
        "failure_rate": failure_rate,
        "avg_response_time": row["Average Response Time"],
        "median_response_time": row["Median Response Time"],
        "min_response_time": row["Min Response Time"],
        "max_response_time": row["Max Response Time"],
        "p95_response_time": row["95%"],
        "p99_response_time": row["99%"],
        "requests_per_second": row["Requests/s"],
        "failures_per_second": row["Failures/s"],
    })


final_df = pd.DataFrame(rows)

final_df = final_df.sort_values(
    by=["language", "cache_mode", "users"]
)

final_df.to_csv(OUTPUT_FILE, index=False)

print(final_df)
print(f"\nArquivo gerado: {OUTPUT_FILE}")