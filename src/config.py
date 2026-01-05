from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    
    # Ollama
    chat_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    llm_type: str = "ollama"
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Existing fields (keep all)
    gemini_api_key: str = ""
    
    chroma_db_path: str = "./chroma_db"
    database_url: str = "sqlite:///web_automation.db"
    
    playwright_headed: bool = True
    browser_timeout: int = 30000
    max_retries: int = 3
    
    langgraph_log_level: str = "INFO"
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "agentic-web-automation"
    
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars

settings = Settings()
