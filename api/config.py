from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jira_base_url: str
    jira_user: str
    jira_api_token: str

    model_config = {"env_file": "../.env"}


settings = Settings()
