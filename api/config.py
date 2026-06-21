from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jira_base_url: str
    jira_user: str
    jira_password: str
    work_hours_per_day: float = 8.0
    team_utilization_factor: float = 0.8
    velocity_sprint_window: int = 3

    model_config = {"env_file": "../.env"}


settings = Settings()
