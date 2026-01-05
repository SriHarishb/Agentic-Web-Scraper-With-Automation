import chromadb
from typing import List, Dict, Any
from langchain_core.documents import Document
from src.config import settings
from src.logger import logger
from pathlib import Path

class ChromaVectorStore:
    """Chroma vector database wrapper"""
    
    def __init__(self, collection_name: str = "website_knowledge"):
        self.collection_name = collection_name
        
        Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize Chroma
        self.client = chromadb.PersistentClient(path=settings.chroma_db_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Initialized Chroma collection: {collection_name}")
    
    async def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> None:
        """Add documents - compatible with Chroma 0.4+ and 0.5+"""
        if not documents or not embeddings:
            logger.warning("Skipping empty add_documents")
            return
        
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [doc.metadata.get("id", f"doc_{i}") for i, doc in enumerate(documents)]
        
        try:
            self.collection.add_texts(
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(texts)} docs (add_texts API)")
        except AttributeError:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"Added {len(texts)} docs (add API fallback)")
        
        except Exception as e:
            logger.error(f"Chroma add failed: {e}")
            raise
   
    async def search(self, query_embedding: List[float], n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            documents = []
            for i in range(len(results["documents"])):
                documents.append({
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "distance": results["distances"][i]
                })
            
            return documents
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            raise
    
    async def search_by_metadata(self, where: Dict[str, Any], n_results: int = 5) -> List[Dict[str, Any]]:
        """Search by metadata filters"""
        try:
            results = self.collection.get(
                where=where,
                limit=n_results
            )
            
            documents = []
            for i in range(len(results["documents"])):
                documents.append({
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
            
            return documents
        except Exception as e:
            logger.error(f"Error searching by metadata: {str(e)}")
            raise
    
    async def delete_collection(self) -> None:
        """Delete collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
