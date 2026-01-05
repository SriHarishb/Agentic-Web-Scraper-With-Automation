import asyncio
from typing import Dict, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from src.logger import logger


class WebScraperModule:
    """Async web scraper using Playwright for dynamic content"""
    
    def __init__(self, domain: str, depth: int = 3, timeout: int = 30000):
        self.domain = domain
        self.depth = depth
        self.timeout = timeout
        self.visited: Set[str] = set()
        self.scraped_pages: Dict[str, dict] = {}
        self.playwright = None
        self.browser = None
        self.context = None
    
    async def initialize(self):
        """Initialize Playwright browser"""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        logger.info(f"Browser initialized for domain: {self.domain}")
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error during browser close: {e}")
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain"""
        parsed_url = urlparse(url)
        parsed_domain = urlparse(self.domain)
        return parsed_url.netloc == parsed_domain.netloc
    
    async def scrape_page(self, url: str) -> dict:
        """Bulletproof scraper - handles all edge cases"""
        if url in self.visited:
            return self.scraped_pages.get(url, {})
        
        self.visited.add(url)
        logger.info(f"Scraping: {url}")
        
        page = None
        try:
            # DOUBLE CHECK context exists
            if not self.context:
                logger.error(" NO CONTEXT")
                return {"url": url, "error": "No browser context", "status": "error"}
            
            page = await self.context.new_page()
            if not page:
                logger.error(" NO PAGE CREATED")
                return {"url": url, "error": "Failed to create page", "status": "error"}
            
            logger.debug(f" Page created: {page}")
            
            # Navigate SAFELY
            logger.debug(f"Goto {url}")
            response = await page.goto(url, timeout=15000)
            if not response:
                logger.error(" NO RESPONSE")
                return {"url": url, "error": "No HTTP response", "status": "error"}
            
            logger.debug(f" Response {response.status}")
            
            # Wait for content
            await asyncio.sleep(1.5)
            
            # CHECK PAGE STILL ALIVE
            if page.is_closed():
                logger.error(" PAGE CLOSED DURING WAIT")
                return {"url": url, "error": "Page closed unexpectedly", "status": "error"}
            
            # SAFE content extraction
            try:
                html = await page.content()
                if not html or len(html) < 100:
                    logger.warning(f"Empty HTML for {url}")
                    return {"url": url, "error": "Empty page content", "status": "error"}
            except Exception as content_err:
                logger.error(f" content() failed: {content_err}")
                return {"url": url, "error": str(content_err), "status": "error"}
            
            # SAFE title
            title = "No title"
            try:
                title = await page.title()
            except:
                pass
            
            # SAFE forms - NO JS EVALUATE
            soup = BeautifulSoup(html, "html.parser")
            forms = []
            for form in soup.find_all("form"):
                form_data = {
                    "id": form.get("id") or "form-unknown",
                    "action": form.get("action", ""),
                    "method": form.get("method", "GET"),
                    "fields": []
                }
                for field in form.find_all(["input", "textarea", "select"]):
                    if field.get("name"):
                        form_data["fields"].append({
                            "name": field.get("name"),
                            "type": field.get("type", "text"),
                            "required": field.has_attr("required")
                        })
                if form_data["fields"]:
                    forms.append(form_data)
            
            page_data = {
                "url": url,
                "title": title,
                "html": html[:30000],  # Truncate
                "forms": forms,
                "status": "success"
            }
            
            self.scraped_pages[url] = page_data
            logger.info(f" {url} ({len(forms)} forms)")
            return page_data
            
        except Exception as e:
            logger.error(f" {url}: {str(e)}")
            return {"url": url, "error": str(e), "status": "error"}
        
        finally:
            if page:
                try:
                    await page.close()
                    logger.debug(f"Page closed for {url}")
                except Exception as close_err:
                    logger.debug(f"Page close failed {close_err}")


    
    async def scrape(self) -> Dict[str, dict]:
        """Scrape domain starting from root URL"""
        try:
            await self.initialize()
            
            to_visit = [self.domain]
            current_depth = 0
            
            while to_visit and current_depth < self.depth:
                next_level = []
                
                for url in to_visit[:5]:  # Limit concurrent
                    if url not in self.visited:
                        page_data = await self.scrape_page(url)
                        
                        if page_data.get("status") == "success":
                            # Extract links for next level
                            soup = BeautifulSoup(page_data["html"], "html.parser")
                            for link in soup.find_all("a", href=True):
                                link_url = urljoin(url, link["href"])
                                if self._is_same_domain(link_url) and link_url not in self.visited:
                                    next_level.append(link_url)
                
                to_visit = list(set(next_level))[:10]  # Limit depth
                current_depth += 1
            
            logger.info(f"Scraping complete. Total pages: {len(self.scraped_pages)}")
            return self.scraped_pages
            
        finally:
            await self.close()


if __name__ == "__main__":
    async def test_scraper():
        scraper = WebScraperModule("https://httpbin.org", timeout=10000)
        pages = await scraper.scrape()
        print(f" Scraped {len(pages)} pages:")
        for url, data in list(pages.items())[:3]:
            print(f"  - {url}: {data.get('status')}")

    asyncio.run(test_scraper())
