import argparse
import os
import subprocess

CONTAINER = "av2-computacao-distribuida-locust-1"
VALID_SCENARIOS = {"image_1mb", "text_400kb", "image_300kb", "all"}


def parse_args():
    parser = argparse.ArgumentParser(description="Executa testes Locust em container Docker.")

    parser.add_argument("--scenarios", nargs="+", required=True)
    parser.add_argument("--users", nargs="+", type=int, required=True)
    parser.add_argument("--instances", nargs="+", type=int, required=True)
    parser.add_argument("--run-time", default="10s")
    parser.add_argument("--host", default="http://nginx")
    parser.add_argument("--results-dir", default="results")

    return parser.parse_args()


def validate_args(args):
    invalid = [scenario for scenario in args.scenarios if scenario not in VALID_SCENARIOS]

    if invalid:
        raise ValueError(f"Cenários inválidos: {invalid}")

    if any(users <= 0 for users in args.users):
        raise ValueError("A quantidade de usuários deve ser maior que 0.")

    if any(instances <= 0 for instances in args.instances):
        raise ValueError("A quantidade de instâncias deve ser maior que 0.")


def ensure_results_dir(path):
    os.makedirs(path, exist_ok=True)


def run_command(command, check=True):
    return subprocess.run(command, check=check)


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
        "--no-recreate",
    ])


def cleanup_csv(results_dir, scenario, users, instances):
    prefix = f"/mnt/locust/{results_dir}/{scenario}_{users}_inst{instances}"

    command = (
        f"rm -f "
        f"{prefix}_history.csv "
        f"{prefix}_failures.csv "
        f"{prefix}_exceptions.csv"
    )

    run_command(
        ["docker", "exec", CONTAINER, "sh", "-c", command],
        check=False,
    )


def run_locust(scenario, users, instances, run_time, host, results_dir):
    ramp = users
    prefix = f"/mnt/locust/{results_dir}/{scenario}_{users}_inst{instances}"

    locust_command = (
        f"SCENARIO={scenario} "
        f"locust -f /mnt/locust/locustfile.py "
        f"--host={host} "
        f"--headless "
        f"-u {users} "
        f"-r {ramp} "
        f"--run-time {run_time} "
        f"--csv={prefix}"
    )

    print(f"[RUN] inst={instances} scenario={scenario} users={users}")

    result = run_command(
        ["docker", "exec", CONTAINER, "sh", "-c", locust_command],
        check=False,
    )

    cleanup_csv(results_dir, scenario, users, instances)

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

        for scenario in args.scenarios:
            for users in args.users:
                run_locust(
                    scenario=scenario,
                    users=users,
                    instances=instances,
                    run_time=args.run_time,
                    host=args.host,
                    results_dir=args.results_dir,
                )


if __name__ == "__main__":
    main()