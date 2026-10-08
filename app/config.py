from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str = "wallet"
    postgres_password: str = "wallet"
    postgres_db: str = "wallet"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
