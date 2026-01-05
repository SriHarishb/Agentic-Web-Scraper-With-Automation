import asyncio
import json
from pathlib import Path
from typing import Dict

from src.scraper.web_scraper import WebScraperModule
from src.knowledge_base.retriever import KnowledgeBaseBuilder
from src.agent.graph import WebAutomationAgent
from src.config import settings
from src.logger import logger

async def main():
    """Main entry point - Full agentic LMS login"""
    
    # Create directories
    Path("screenshots").mkdir(exist_ok=True)
    Path("chromadb").mkdir(exist_ok=True)
    
    logger.info("Starting Agentic Web Automation System")
    
    # Configuration
    domain = "https://news.ycombinator.com/login"
    task = "Log into HackerNews. Username is '' . Password is '' ."
    
    # Step 1: Scrape website
    logger.info("Step 1: Scraping website...")
    scraper = WebScraperModule(domain=domain, depth=2)
    scraped_pages = await scraper.scrape()
    logger.info(f"Scraped {len(scraped_pages)} pages")
    
    if not scraped_pages:
        logger.error("No pages scraped; aborting.")
        return
    
    # Step 2: Build knowledge base
    logger.info("Step 2: Building knowledge base...")
    kb_builder = KnowledgeBaseBuilder()
    await kb_builder.build_from_scraped_pages(scraped_pages)
    logger.info("Knowledge base built")
    
    # Test RAG retrieval
    logger.info("Testing RAG retrieval...")
    results = await kb_builder.search("login form")
    logger.info(f"RAG Results: {type(results)} len={len(results) if results else 0}")
    
    # Clean results display
    flat_results = results[0] if results and isinstance(results[0], list) else results or []
    for i, r in enumerate(flat_results[:3]):
        try:
            meta = r.get('metadata', {})
            if isinstance(meta, list): 
                meta = meta[0] if meta else {}
            url = meta.get('source_url', f'chunk-{i}')[:60]
            dist = r.get('distance', 0.0)
            logger.info(f"  - {url}... (dist: {dist:.3f})")
        except:
            logger.info(f"  - Raw result {i}: {type(r)}")
    
    # Step 3: Agent execution with RAG context
    logger.info("Step 3: Launching agent...")
    agent = WebAutomationAgent(kb_builder)
    
    # Execute with context injection
    result = await agent.execute_task_with_context(task, domain, kb_builder)
    
    # Results
    logger.info(f"Status: {'SUCCESS' if result.get('success') else 'FAILED'}")
    print("\n" + "="*60)
    print("AUTOMATION COMPLETE")
    print("="*60)
    print(f"Status: {'SUCCESS' if result.get('success') else 'FAILED'}")
    print(f"Error: {result.get('error', 'None')}")
    print(f"Steps completed: {len(result.get('steps_completed', []))}")
    print(f"Screenshots: {result.get('screenshots', [])}")
    if result.get('agent_reasoning'):
        print(f"Agent plan: {result['agent_reasoning'][:200]}...")
    print("="*60)
    
    # Save result
    result_path = Path("screenshots") / f"result-{result.get('execution_id', 'unknown')[:8]}.json"
    result_path.write_text(json.dumps(result, indent=2, default=str))
    logger.info(f"Full result saved: {result_path}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Cancelled by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
