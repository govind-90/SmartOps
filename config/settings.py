"""Configuration management for Change Management Analysis System."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings and configuration."""

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT / "logs"
    POLICIES_DIR = PROJECT_ROOT / "policies"
    SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"

    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    POLICIES_DIR.mkdir(exist_ok=True)
    SAMPLE_DATA_DIR.mkdir(exist_ok=True)

    # Database configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(DATA_DIR / "changes.db"))
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", str(DATA_DIR / "chroma_db"))

    # Logging configuration
    LOGS_PATH: str = os.getenv("LOGS_PATH", str(LOGS_DIR))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = f"{LOGS_PATH}/app.log"

    # Groq API configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    # LLM parameters
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))

    # Risk scoring thresholds
    RISK_APPROVE_THRESHOLD: int = int(os.getenv("RISK_APPROVE_THRESHOLD", "40"))
    RISK_REJECT_THRESHOLD: int = int(os.getenv("RISK_REJECT_THRESHOLD", "70"))

    # RAG configuration
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # Policy documents
    POLICY_CHANGE_MANAGEMENT: str = str(POLICIES_DIR / "change_management_policy.txt")
    POLICY_SECURITY: str = str(POLICIES_DIR / "security_policy.txt")
    POLICY_DEPLOYMENT: str = str(POLICIES_DIR / "deployment_standards.txt")

    # Bulk processing
    BULK_PROCESSING_DELAY_SECONDS: float = float(
        os.getenv("BULK_PROCESSING_DELAY_SECONDS", "1")
    )
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "3"))

    # Validation
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. Please configure it in .env file."
        )

    class Config:
        """Pydantic config."""
        case_sensitive = True


# Global settings instance
settings = Settings()
