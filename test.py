import asyncio
from src.browser.playwright_adapter import PlaywrightAdapter
from src.logger import logger

async def test_browser():
    logger.info("=== BROWSER TEST ===")
    browser = PlaywrightAdapter()
    
    try:
        await browser.initialize()
        await browser.navigate("http://lms2.ai.saveetha.in/login/index.php")
        await browser.screenshot("test_lms.png")
        print("✅ LMS PAGE LOADED!")
        print(f"Current URL: {browser.page.url}")
        print("Screenshot: test_lms.png")
        
    except Exception as e:
        print(f"❌ Browser error: {e}")
    finally:
        await browser.close()
        logger.info("Browser test complete")

if __name__ == "__main__":
    asyncio.run(test_browser())
