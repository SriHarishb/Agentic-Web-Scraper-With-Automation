from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import settings
from src.logger import logger

class EmbeddingService:
    """Local embeddings - no API quota issues"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # Use GPU if available
        )
        logger.info(f"Initialized local embeddings: {model_name} (CPU)")
    
    async def embed_text(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
