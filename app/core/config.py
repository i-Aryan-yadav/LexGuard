import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Contract Risk Intelligence"
    DATABASE_URL: str = "sqlite+aiosqlite:///./contract_risk.db"
    GEMINI_API_KEY: str = "AIzaSyCVMMTwv2U0MTTLtncxsqhPO4VooQ84GqY"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # ── LegalBERT Configuration ──────────────────────────────────────────────
    LEGALBERT_MODEL_NAME: str = "nlpaueb/legal-bert-base-uncased"
    LEGALBERT_ENABLED: bool = True
    LEGALBERT_SCORE_WEIGHT: float = 0.4
    RULE_SCORE_WEIGHT: float = 0.6

    # Performance & Guardrails
    HIGH_RULE_SCORE_THRESHOLD: float = 0.75
    LARGE_CONTRACT_CLAUSE_THRESHOLD: int = 150
    EMBEDDING_CACHE_ENABLED: bool = True

    # Experimental
    FINE_TUNE_MODE: bool = False
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

settings = Settings()
