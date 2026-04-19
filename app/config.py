from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "WBS MVP Backend"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "sqlite:///./wbs.db"
    upload_dir: str = "./uploads"

    admin_default_username: str = "admin"
    admin_default_password: str = "admin123"

    jwt_secret_key: str = "change-me-super-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "embeddinggemma:latest"
    ollama_llm_model: str = "yinw1590/gemma4-e2b-text:latest"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "wbs_knowledge_base"
    qdrant_collection_violation: str = "wbs_violation"
    qdrant_collection_oos: str = "wbs_oos"

    kb_file: str = "./plan/Knowledge Base.xlsx"
    rag_top_k: int = 5
    rag_min_score: float = 0.25
    rag_min_score_violation: float = 0.17
    rag_min_score_oos: float = 0.23
    rag_group_margin: float = 0.04

    report_pin_max_attempts: int = 5
    report_pin_lock_minutes: int = 15


settings = Settings()
