import os
from locust import HttpUser, between, task

DEFAULT_HOST = "http://nginx"

POST_IMAGE_1MB_ID = os.getenv("POST_IMAGE_1MB_ID", "47")
POST_TEXT_400KB_ID = os.getenv("POST_TEXT_400KB_ID", "15")
POST_IMAGE_300KB_ID = os.getenv("POST_IMAGE_300KB_ID", "43")

SCENARIO = os.getenv("SCENARIO", "image_300kb")


class WordPressTestUser(HttpUser):
    host = os.getenv("LOCUST_HOST", DEFAULT_HOST)
    wait_time = between(1, 2)

    @task
    def run_selected_scenario(self):
        if SCENARIO == "image_1mb":
            self._get_post(POST_IMAGE_1MB_ID, "GET post imagem ~1MB")

        elif SCENARIO == "text_400kb":
            self._get_post(POST_TEXT_400KB_ID, "GET post texto ~400KB")

        elif SCENARIO == "image_300kb":
            self._get_post(POST_IMAGE_300KB_ID, "GET post imagem ~300KB")

        elif SCENARIO == "all":
            self._get_post(POST_IMAGE_1MB_ID, "GET post imagem ~1MB")
            self._get_post(POST_TEXT_400KB_ID, "GET post texto ~400KB")
            self._get_post(POST_IMAGE_300KB_ID, "GET post imagem ~300KB")

        else:
            raise ValueError(f"Cenário inválido: {SCENARIO}")

    def _get_post(self, post_id: str, request_name: str):
        with self.client.get(
            f"/?p={post_id}",
            name=request_name,
            catch_response=True
        ) as response:
            if response.status_code >= 400:
                response.failure(f"Falha no GET: HTTP {response.status_code}")