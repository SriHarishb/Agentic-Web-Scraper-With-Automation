from typing import List, Dict, Any
from langchain_core.documents import Document
from src.knowledge_base.embedder import EmbeddingService
from src.knowledge_base.chroma_store import ChromaVectorStore
from src.logger import logger
from sentence_transformers import SentenceTransformer
import numpy as np


class KnowledgeBaseBuilder:
    """Build and manage knowledge base from scraped content"""
    
    def __init__(self):
        try:
            self.embedder = EmbeddingService()
        except:
            # Fallback to local embeddings
            logger.info("Using local SentenceTransformer embeddings")
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.vector_store = ChromaVectorStore()
        self.embedding_dim = 384  # MiniLM dimension
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks
    
    async def build_from_scraped_pages(self, scraped_pages: Dict[str, dict]) -> None:
        logger.info(f"Building KB from {len(scraped_pages)} pages")
        
        documents = []
        for url, page_data in scraped_pages.items():
            if page_data.get("status") == "success":
                # Rich content for agent
                content = (
                    f"URL: {url}\n"
                    f"TITLE: {page_data.get('title', 'No title')}\n"
                    f"FORMS: {page_data.get('forms', [])}\n"
                    f"INPUTS: {page_data.get('inputs', [])}\n"
                    f"LINKS: {page_data.get('links', [])[:5]}\n"
                    f"HEADINGS: {page_data.get('headings', [])[:3]}"
                )
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "source_url": url,
                        "title": page_data.get('title', ''),
                        "forms": page_data.get("forms", []),
                        "inputs": page_data.get("inputs", [])
                    }
                )
                documents.append(doc)
        
        if documents:
            # Local embeddings
            embeddings = []
            for doc in documents:
                emb = self.embedder.encode(doc.page_content).tolist()
                embeddings.append(emb)
            
            await self.vector_store.add_documents(documents, embeddings)
            logger.info(f"Stored {len(documents)} docs with local embeddings")
        else:
            logger.warning("No valid pages found")
    
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search"""
        emb = self.embedder.encode([query])[0].tolist()
        return await self.vector_store.similarity_search(emb, k=k)
