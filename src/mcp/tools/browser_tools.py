import asyncio
from typing import Dict, Any
from src.browser.playwright_adapter import PlaywrightAdapter

class BrowserTools:
    """Collection of browser automation tools"""
    
    def __init__(self, browser_adapter: PlaywrightAdapter):
        self.browser = browser_adapter
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL"""
        try:
            await self.browser.navigate(url)
            state = await self.browser.get_page_state()
            return {"success": True, "message": f"Navigated to {url}", "page_state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fill_form(self, form_selector: str, field_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form fields"""
        try:
            await self.browser.fill_form(form_selector, field_data)
            state = await self.browser.get_page_state()
            return {"success": True, "message": f"Filled {len(field_data)} fields", "page_state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """Click element"""
        try:
            await self.browser.click(selector)
            await asyncio.sleep(0.5)  # Brief wait for potential changes
            state = await self.browser.get_page_state()
            return {"success": True, "message": f"Clicked {selector}", "page_state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def wait_for(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Wait for element"""
        try:
            await self.browser.wait_for_element(selector, timeout)
            state = await self.browser.get_page_state()
            return {"success": True, "message": f"Element {selector} found", "page_state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def submit_form(self, form_selector: str) -> Dict[str, Any]:
        """Submit form"""
        try:
            await self.browser.submit_form(form_selector)
            await asyncio.sleep(2)  # Wait for form submission
            state = await self.browser.get_page_state()
            return {"success": True, "message": "Form submitted", "page_state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_text(self, selector: str) -> Dict[str, Any]:
        """Extract text from element"""
        try:
            text = await self.browser.extract_text(selector)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_page_state(self) -> Dict[str, Any]:
        """Get current page state"""
        try:
            state = await self.browser.get_page_state()
            return {"success": True, "page_state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self) -> Dict[str, Any]:
        """Take screenshot"""
        try:
            path = await self.browser.screenshot()
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def select_option(self, selector: str, value: str) -> Dict[str, Any]:
        """Select dropdown option"""
        try:
            await self.browser.select_option(selector, value)
            state = await self.browser.get_page_state()
            return {"success": True, "message": f"Selected {value}", "page_state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
