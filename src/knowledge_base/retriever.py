from typing import List, Dict, Any
from langchain_core.documents import Document
from src.knowledge_base.embedder import EmbeddingService
from src.knowledge_base.chroma_store import ChromaVectorStore
from src.logger import logger

class KnowledgeBaseBuilder:
    """Build and manage knowledge base from scraped content"""
    
    def __init__(self):
        self.embedder = EmbeddingService()
        self.vector_store = ChromaVectorStore()
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks
    
    async def build_from_scraped_pages(self, scraped_pages: Dict[str, dict]) -> None:
        """Build knowledge base from scraped pages"""
        documents = []
        embeddings = []
        
        logger.info(f"Building knowledge base from {len(scraped_pages)} pages")
        
        for url, page_data in scraped_pages.items():
            if page_data.get("status") != "success":
                continue
            
            # Extract content
            title = page_data.get("title", "")
            html = page_data.get("html", "")
            forms = page_data.get("forms", [])
            
            # Create chunks
            chunks = self._chunk_text(html, chunk_size=1500)
            
            for chunk_idx, chunk in enumerate(chunks):
                doc_id = f"{url.replace('/', '_')}_{chunk_idx}"
                
                # Create metadata
                metadata = {
                    "id": doc_id,
                    "source_url": url,
                    "page_title": title,
                    "chunk_index": chunk_idx,
                    "has_forms": len(forms) > 0,
                    "form_count": len(forms)
                }
                
                document = Document(page_content=chunk, metadata=metadata)
                documents.append(document)
        
        # Embed all documents
        logger.info(f"Embedding {len(documents)} document chunks...")
        texts = [doc.page_content for doc in documents]
        embeddings = await self.embedder.embed_documents(texts)
        
        # Add to vector store
        await self.vector_store.add_documents(documents, embeddings)
        logger.info("Knowledge base built successfully")
    
    async def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        try:
            query_embedding = await self.embedder.embed_text(query)
            results = await self.vector_store.search(query_embedding, n_results)
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            raise
