from locust import HttpUser, between, task


class ApiUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health(self) -> None:
        self.client.get("/api/v1/health")

    @task
    def dashboard(self) -> None:
        self.client.get("/")

    @task
    def observations(self) -> None:
        self.client.get("/api/v1/space/observations?limit=20")

    @task
    def daily_summary(self) -> None:
        self.client.get("/api/v1/space/daily-summary")

    @task
    def neo_analytics(self) -> None:
        self.client.get("/api/v1/space/analytics/neo")
