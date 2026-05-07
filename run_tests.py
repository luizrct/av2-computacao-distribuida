import argparse
import os
import subprocess
import time

LOCUST_SERVICE = "locust"
VALID_SCENARIOS = {"low", "medium", "high", "hybrid"}


def parse_args():
    parser = argparse.ArgumentParser(description="Executa testes Locust em container Docker.")

    parser.add_argument("--scenarios", nargs="+", required=True)
    parser.add_argument("--users", nargs="+", type=int, required=True)
    parser.add_argument("--instances", nargs="+", type=int, required=True)
    parser.add_argument("--run-time", default="30s")
    parser.add_argument("--host", default="http://nginx")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--spawn-rate", type=int, default=None)
    parser.add_argument("--warmup-seconds", type=int, default=10)

    return parser.parse_args()


def validate_args(args):
    invalid = [scenario for scenario in args.scenarios if scenario not in VALID_SCENARIOS]

    if invalid:
        raise ValueError(f"Cenários inválidos: {invalid}")

    if any(users <= 0 for users in args.users):
        raise ValueError("A quantidade de usuários deve ser maior que 0.")

    if any(instances <= 0 for instances in args.instances):
        raise ValueError("A quantidade de instâncias deve ser maior que 0.")


def run_command(command, check=True):
    return subprocess.run(command, check=check)


def ensure_results_dir(path):
    os.makedirs(path, exist_ok=True)


def start_stack():
    run_command(["docker", "compose", "up", "-d"])


def scale_wordpress(instances):
    run_command([
        "docker",
        "compose",
        "up",
        "-d",
        "--scale",
        f"wordpress_app={instances}",
    ])


def wait_after_scale(seconds):
    print(f"[WAIT] aguardando {seconds}s para estabilização")
    time.sleep(seconds)


def cleanup_previous_csv(results_dir, scenario, users, instances):
    prefix = f"/mnt/locust/{results_dir}/{scenario}_{users}_inst{instances}"

    command = (
        f"rm -f "
        f"{prefix}_stats.csv "
        f"{prefix}_stats_history.csv "
        f"{prefix}_failures.csv "
        f"{prefix}_exceptions.csv"
    )

    run_command(
        ["docker", "compose", "exec", "-T", LOCUST_SERVICE, "sh", "-c", command],
        check=False,
    )


def run_locust(scenario, users, instances, run_time, host, results_dir, spawn_rate):
    prefix = f"/mnt/locust/{results_dir}/{scenario}_{users}_inst{instances}"

    if spawn_rate is None:
        # spawn_rate = max(1, users // 10)
        spawn_rate = users

    cleanup_previous_csv(results_dir, scenario, users, instances)

    locust_command = (
        f"SCENARIO={scenario} "
        f"locust -f /mnt/locust/locustfile.py "
        f"--host={host} "
        f"--headless "
        f"-u {users} "
        f"-r {spawn_rate} "
        f"--run-time {run_time} "
        f"--csv={prefix}"
    )

    print(
        f"[RUN] inst={instances} "
        f"scenario={scenario} "
        f"users={users} "
        f"spawn_rate={spawn_rate}/s"
    )

    result = run_command(
        ["docker", "compose", "exec", "-T", LOCUST_SERVICE, "sh", "-c", locust_command],
        check=False,
    )

    if result.returncode != 0:
        print(
            f"[WARN] Locust finalizou com erro: "
            f"inst={instances}, scenario={scenario}, users={users}"
        )


def main():
    args = parse_args()
    validate_args(args)

    ensure_results_dir(args.results_dir)
    start_stack()

    for instances in args.instances:
        print(f"[SCALE] wordpress_app={instances}")
        scale_wordpress(instances)
        wait_after_scale(args.warmup_seconds)

        for scenario in args.scenarios:
            for users in args.users:
                run_locust(
                    scenario=scenario,
                    users=users,
                    instances=instances,
                    run_time=args.run_time,
                    host=args.host,
                    results_dir=args.results_dir,
                    spawn_rate=args.spawn_rate,
                )


if __name__ == "__main__":
    main()