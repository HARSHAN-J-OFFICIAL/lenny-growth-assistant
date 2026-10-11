"""
Application configuration and environment settings management using Pydantic Settings.
"""

from pathlib import Path
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings loaded from environment variables and .env files.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Meta
    PROJECT_NAME: str = "The Lenny Growth Assistant"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS Configuration
    ALLOWED_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="Origins permitted to make cross-origin requests",
    )

    # Persistence / Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./lenny_assistant.db",
        description="Async SQLAlchemy database connection URL",
    )

    # Local LLM (Ollama)
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Base URL for local Ollama daemon",
    )
    OLLAMA_DEFAULT_MODEL: str = Field(
        default="llama3.2",
        description="Default local model identifier in Ollama",
    )

    # Cloud LLM Providers (Optional credentials and configurable defaults)
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude provider toggle",
    )
    ANTHROPIC_DEFAULT_MODEL: str = Field(
        default="claude-sonnet-4-6",
        description="Default Anthropic Claude model identifier",
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key for OpenAI provider toggle",
    )
    OPENAI_DEFAULT_MODEL: str = Field(
        default="gpt-4o",
        description="Default OpenAI model identifier",
    )
    # Groq Cloud Provider (Free-Tier High-Speed Inference)
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="Groq API key for free-tier cloud inference",
    )
    GROQ_MODEL: str = Field(
        default="openai/gpt-oss-20b",
        description="Default Groq cloud model identifier",
    )
    GROQ_BASE_URL: str = Field(
        default="https://api.groq.com/openai/v1",
        description="Base URL for Groq OpenAI-compatible API endpoint",
    )

    # Knowledge Base & Retrieval Engine
    TRANSCRIPTS_DATA_DIR: str = Field(
        default="",
        description="Path to cloned Lenny podcast transcripts directory",
    )
    INDICES_STORAGE_DIR: str = Field(
        default="",
        description="Path to store persistent vector and lexical index artifacts",
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Embedding model name for fastembed vector indexing",
    )
    CHUNK_TARGET_WORDS: int = Field(
        default=180,
        description="Target word count for conversational chunk grouping",
    )
    CHUNK_OVERLAP_WORDS: int = Field(
        default=35,
        description="Word overlap between adjacent conversational chunks",
    )
    RRF_K: int = Field(
        default=60,
        description="Reciprocal Rank Fusion smoothing parameter k",
    )
    EVIDENCE_THRESHOLD: float = Field(
        default=0.012,
        description="Minimum reciprocal score required to declare relevant evidence found",
    )
    DEFAULT_TOP_K: int = Field(
        default=5,
        description="Default number of passages to return in retrieval results",
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Normalize comma-separated strings into a validated list of origin strings.
        """
        if isinstance(v, str):
            # Split comma-separated string if provided as env var
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def transcripts_dir(self) -> Path:
        """Resolve absolute path to transcripts directory."""
        if self.TRANSCRIPTS_DATA_DIR:
            return Path(self.TRANSCRIPTS_DATA_DIR).resolve()
        current_file = Path(__file__).resolve()
        for parent in [current_file.parents[2], current_file.parents[3], current_file.parents[1]]:
            candidate = parent / "data" / "transcripts"
            if candidate.exists():
                return candidate
        return (Path.cwd() / "data" / "transcripts").resolve()

    @property
    def indices_dir(self) -> Path:
        """Resolve absolute path to local indices storage directory."""
        if self.INDICES_STORAGE_DIR:
            p = Path(self.INDICES_STORAGE_DIR).resolve()
        else:
            p = self.transcripts_dir.parent / "indices"
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
