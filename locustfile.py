from locust import HttpUser, task, between

class WordPressTestUser(HttpUser):
    wait_time = between(1, 2)

    # CENÁRIO 1: Post com imagem de 1MB
    @task
    def test_image_1mb(self):
        self.client.get("/?p=12") # Substitua pelo ID do post correto

    # CENÁRIO 2: Post com texto de 400KB
    # @task
    # def test_text_400kb(self):
    #     self.client.get("/?p=2") # Substitua pelo ID do post correto

    # CENÁRIO 3: Post com imagem de 300KB
    # @task
    # def test_image_300kb(self):
    #     self.client.get("/?p=3") # Substitua pelo ID do post correto