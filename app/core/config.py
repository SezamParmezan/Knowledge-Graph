from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    #App
    app_name: str = Field("KnowledgeGraph")
    debug: bool = Field(default = True)
    host: str = Field("127.0.0.1")
    port: int = Field(8000)


    #AI API
    ai_api_key: str = Field(default = "")
    ai_api_model: str = Field(default = "gemini-1.5-flash")


    #Paths
    chroma_db_path: str = Field(default = "data/chroma")
    cache_path: str = Field(default = "data/cache")


    #Scraper
    scraper_timeout: int = Field(default = 30)
    scraper_max_chars: int = Field(default = 500_000)


    #Graph
    graph_max_nodes: int = Field(default = 50)
    graph_max_depth: int = Field(default = 3)


    #Logging
    log_level: str = Field(default = "DEBUG")
    log_file: str = Field(default = "logs/app.log")


    @property
    def is_dev(self) -> bool:
        return self.debug


    def ensure_dirs(self) -> None:
        from pathlib import Path
        for p in [self.chroma_db_path, self.cache_path, "logs", "data"]:
            Path(p).mkdir(parents=True, exist_ok=True)


settings = Settings() #type: ignore