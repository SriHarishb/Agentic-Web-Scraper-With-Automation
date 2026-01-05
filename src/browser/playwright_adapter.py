from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from src.config import settings
from src.logger import logger
from typing import Optional

class PlaywrightAdapter:
    """Wrapper around Playwright for browser automation"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def initialize(self):
        """Initialize Playwright and launch browser"""
        try:
            logger.info("1. Starting Playwright...")
            self.playwright = await async_playwright().start()
            logger.info(f"2. Playwright: {self.playwright is not None}")
            
            logger.info("3. Launching Chromium...")
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info(f"4. Browser: {self.browser is not None}")
            
            logger.info("5. New context...")
            self.context = await self.browser.new_context()
            logger.info(f"6. Context: {self.context is not None}")
            
            logger.info("7. New page...")
            self.page = await self.context.new_page()
            logger.info(f"8. Page: {self.page is not None}")
            
            if self.page:
                self.page.set_default_timeout(30000)
                logger.info("ALL READY")
            else:
                raise Exception("Page is None")
                
        except Exception as e:
            logger.error(f"FAILED at: {type(e).__name__}: {e}")
            logger.error(f"State: pw={self.playwright}, browser={self.browser}, ctx={self.context}, page={self.page}")
            await self.close()
            raise

    async def navigate(self, url: str) -> str:
        """Navigate to URL"""
        try:
            await self.page.goto(url, wait_until="networkidle")
            logger.info(f"Navigated to {url}")
            return self.page.url
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            raise
    
    async def fill_form(self, form_selector: str, field_data: dict) -> None:
        """Fill form fields - FIXED selector logic"""
        try:
            logger.info(f"Filling form {form_selector} with {len(field_data)} fields")
            
            for field_name, value in field_data.items():
                # FIXED: Use field_name directly as selector (e.g., "#username")
                # Previously used f"{form_selector} [name='{field_name}']" which broke IDs
                field_selector = field_name 
                await self.page.wait_for_selector(field_selector, timeout=10000)
                await self.page.fill(field_selector, str(value))
                logger.info(f"Filled {field_selector} with {value}")
                
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            raise

        async def fill(self, selector: str, value: str) -> None:
            """Fill field - supports comma-separated fallback selectors"""
            try:
                # Try to wait for the group of selectors
                # Playwright supports "input[name='a'], input[name='b']" natively!
                # It will wait for ANY of them to appear.
                
                logger.info(f"Attempting to fill: {selector}")
                element = await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                
                if element:
                    await element.fill(str(value))
                    logger.info(f"Filled {selector} with '{value}'")
                else:
                    raise Exception("Element not found")
                    
            except Exception as e:
                logger.error(f"Error filling {selector}: {e}")
                raise

    
    async def click(self, selector: str) -> None:
        """Click element"""
        try:
            await self.page.click(selector)
            logger.info(f"Clicked {selector}")
        except Exception as e:
            logger.error(f"Error clicking {selector}: {str(e)}")
            raise
    
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> None:
        """Wait for element to appear"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout or settings.browser_timeout)
            logger.info(f"Element {selector} appeared")
        except Exception as e:
            logger.error(f"Error waiting for {selector}: {str(e)}")
            raise
    
    async def submit_form(self, form_selector: str) -> None:
        """Submit form"""
        try:
            submit_btn = await self.page.query_selector(f"{form_selector} [type='submit']")
            if submit_btn:
                await submit_btn.click()
            else:
                await self.page.evaluate(f"document.querySelector('{form_selector}').submit()")
            
            logger.info(f"Submitted form {form_selector}")
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            raise
    
    async def extract_text(self, selector: str) -> str:
        """Extract text from element"""
        try:
            text = await self.page.text_content(selector)
            return text or ""
        except Exception as e:
            logger.error(f"Error extracting text from {selector}: {str(e)}")
            return ""
    
    async def get_page_state(self) -> dict:
        """Get current page state"""
        try:
            html = await self.page.content()
            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "html": html[:1000]  # First 1000 chars
            }
        except Exception as e:
            logger.error(f"Error getting page state: {str(e)}")
            return {}
    
    async def screenshot(self, path: str = None) -> str:
        """Take screenshot"""
        try:
            if not path:
                path = f"screenshots/screenshot_{id(self)}.png"
            
            await self.page.screenshot(path=path)
            logger.info(f"Screenshot saved to {path}")
            return path
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            raise
    
    async def select_option(self, selector: str, value: str) -> None:
        """Select dropdown option"""
        try:
            await self.page.select_option(selector, value)
            logger.info(f"Selected '{value}' in {selector}")
        except Exception as e:
            logger.error(f"Error selecting option: {str(e)}")
            raise
    
    async def close(self):
        """Close browser"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
