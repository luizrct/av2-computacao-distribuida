import argparse
import os
import subprocess
import time
from pathlib import Path

LOCUST_SERVICE = "locust"

VALID_SCENARIOS = {
    "python",
    "python-cache",
    "ruby",
    "ruby-cache",
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Executa testes de desempenho do Link Extractor usando Locust em container Docker."
    )

    parser.add_argument(
        "--scenarios",
        nargs="+",
        required=True,
        choices=VALID_SCENARIOS,
        help="Cenários: python, python-cache, ruby, ruby-cache",
    )

    parser.add_argument(
        "--users",
        nargs="+",
        type=int,
        required=True,
        help="Lista de quantidades de usuários virtuais. Ex: --users 10 50 100",
    )

    parser.add_argument(
        "--run-time",
        default="30s",
        help="Tempo de execução de cada teste. Ex: 30s, 1m, 5m",
    )

    parser.add_argument(
        "--results-dir",
        default="results/raw",
        help="Diretório onde os CSVs serão salvos.",
    )

    parser.add_argument(
        "--spawn-rate",
        type=int,
        default=None,
        help="Taxa de criação de usuários por segundo. Se omitido, usa o total de usuários.",
    )

    parser.add_argument(
        "--warmup-seconds",
        type=int,
        default=10,
        help="Tempo de espera após subir cada cenário.",
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Reconstrói as imagens antes de executar os testes.",
    )

    parser.add_argument(
        "--down-after-each-scenario",
        action="store_true",
        help="Executa docker compose down -v após cada cenário.",
    )

    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Limpa o Redis antes de cada teste em cenários com cache.",
    )

    return parser.parse_args()


def validate_args(args):
    if any(users <= 0 for users in args.users):
        raise ValueError("A quantidade de usuários deve ser maior que 0.")

    if args.spawn_rate is not None and args.spawn_rate <= 0:
        raise ValueError("O spawn-rate deve ser maior que 0.")

    if args.warmup_seconds < 0:
        raise ValueError("O warmup-seconds não pode ser negativo.")


def run_command(command, check=True):
    print("[CMD]", " ".join(command))
    return subprocess.run(command, check=check)


def ensure_results_dir(path):
    os.makedirs(path, exist_ok=True)


def stop_profile_services(profile):
    services = {
        "python": [
            "api-python",
        ],
        "python-cache": [
            "api-python-cache",
            "redis",
        ],
        "ruby": [
            "api-ruby",
        ],
        "ruby-cache": [
            "api-ruby-cache",
            "redis",
        ],
    }

    run_command(
        [
            "docker",
            "compose",
            "stop",
            *services[profile]
        ],
        check=False,
    )

    run_command(
        [
            "docker",
            "compose",
            "rm",
            "-f",
            *services[profile]
        ],
        check=False,
    )


def start_stack(scenario, rebuild=False):
    PROFILES = {
        "python": "python-api",
        "python-cache": "python-api-cache",
        "ruby": "ruby-api",
        "ruby-cache": "ruby-api-cache",
    }

    profile = PROFILES[scenario]
    command = [
        "docker",
        "compose",
        "--profile",
        profile,
        "up",
        "-d",
        "--remove-orphans",
    ]

    if rebuild:
        command.append("--build")

    run_command(command)


def wait_after_start(seconds):
    print(f"[WAIT] aguardando {seconds}s para estabilização")
    time.sleep(seconds)


def clear_redis_cache():
    result = run_command(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "redis",
            "redis-cli",
            "FLUSHALL",
        ],
        check=False,
    )

    if result.returncode != 0:
        print("[WARN] Não foi possível limpar o Redis. O cenário talvez não use cache.")


def cleanup_previous_csv(results_dir, scenario, users):
    base_path = Path(results_dir)

    files = [
        f"{scenario}_{users}_stats.csv",
        f"{scenario}_{users}_stats_history.csv",
        f"{scenario}_{users}_failures.csv",
        f"{scenario}_{users}_exceptions.csv",
    ]

    for file in files:
        path = base_path / file

        if path.exists():
            path.unlink()


def run_locust(scenario, users, run_time, results_dir, spawn_rate):

    SCENARIO_HOSTS = {
        "python": "http://api-python:5000",
        "python-cache": "http://api-python-cache:5000",
        "ruby": "http://api-ruby:4567",
        "ruby-cache": "http://api-ruby-cache:4567",
    }

    host = SCENARIO_HOSTS[scenario]

    if spawn_rate is None:
        spawn_rate = users

    prefix = f"/mnt/{results_dir}/{scenario}_{users}"

    cleanup_previous_csv(
        results_dir=results_dir,
        scenario=scenario,
        users=users,
    )

    locust_command = [
        "docker",
        "compose",
        "--profile",
        "test",
        "run",
        "--rm",
        LOCUST_SERVICE,
        "-f",
        "/mnt/locust/locustfile.py",
        "--host",
        host,
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "--run-time",
        run_time,
        "--csv",
        prefix,
    ]

    print(
        f"[RUN] scenario={scenario} "
        f"users={users} "
        f"spawn_rate={spawn_rate}/s "
        f"host={host}"
    )

    result = run_command(locust_command, check=False)

    if result.returncode != 0:
        print(
            f"[WARN] Locust finalizou com erro: "
            f"scenario={scenario}, users={users}"
        )


def main():
    args = parse_args()
    validate_args(args)

    ensure_results_dir(args.results_dir)

    for scenario in args.scenarios:
        stop_profile_services(scenario)

        print(f"[START] scenario={scenario}")

        start_stack(
            scenario=scenario,
            rebuild=args.rebuild,
        )

        wait_after_start(args.warmup_seconds)

        for users in args.users:
            if args.clear_cache and "cache" in scenario:
                clear_redis_cache()

            run_locust(
                scenario=scenario,
                users=users,
                run_time=args.run_time,
                results_dir=args.results_dir,
                spawn_rate=args.spawn_rate,
            )

        if args.down_after_each_scenario:
            stop_profile_services(scenario)

    for scenario in args.scenarios:
        stop_profile_services(scenario)

if __name__ == "__main__":
    main()