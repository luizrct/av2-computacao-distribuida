import os
import time
import requests
from locust import HttpUser, between, task

DEFAULT_HOST = "http://nginx"

SCENARIO = os.getenv("SCENARIO", "high")
# SCENARIO = "high"

POSTS = {
    "low": {
        "label": "carga leve imagem ~300KB",
        "requests": [
            {
                "path": os.getenv("POST_IMAGE_300KB_NAME", ""),
                "name": "01 arquivo carga leve imagem ~300KB",
            },
        ],
    },
    "medium": {
        "label": "carga média texto ~500KB",
        "requests": [
            {
                "path": os.getenv("POST_TEXT_500KB_ID", "/?p=6"),
                "name": "01 página carga média texto ~500KB",
            },
        ],
    },
    "high": {
        "label": "carga alta imagem ~2MB",
        "requests": [
            {
                "path": os.getenv("POST_IMAGE_2MB_NAME", ""),
                "name": "01 arquivo carga alta imagem ~2MB",
            },
        ],
    },
}


class WordPressTestUser(HttpUser):
    host = os.getenv("LOCUST_HOST", DEFAULT_HOST)
    wait_time = between(1, 2)

    def on_start(self):
        self.wait_until_wordpress_is_ready()

    def wait_until_wordpress_is_ready(self):
        url = f"{self.host}/"

        for _ in range(60):
            try:
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    return

            except requests.RequestException:
                pass

            time.sleep(2)

        raise RuntimeError("WordPress não ficou pronto dentro do tempo limite.")

    @task
    def run_selected_scenario(self):
        if SCENARIO == "hybrid":
            self.run_hybrid_scenario()
            return

        self.run_single_scenario(SCENARIO)

    def run_single_scenario(self, scenario_name: str):
        scenario = POSTS.get(scenario_name)

        if scenario is None:
            valid_scenarios = ", ".join([*POSTS.keys(), "hybrid"])
            raise ValueError(
                f"Cenário inválido: {scenario_name}. "
                f"Cenários válidos: {valid_scenarios}"
            )

        self.execute_requests(scenario["requests"])

    def run_hybrid_scenario(self):
        for scenario in POSTS.values():
            self.execute_requests(scenario["requests"])

    def execute_requests(self, requests_config: list[dict]):
        for request_config in requests_config:
            self.get_resource(
                path=request_config["path"],
                request_name=request_config["name"],
            )

    def get_resource(self, path: str, request_name: str):
        with self.client.get(
            path,
            name=request_name,
            timeout=30,
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"Falha no GET: HTTP {response.status_code}")
            else:
                response.success()