from bs4 import BeautifulSoup
from typing import Dict, List, Any

class WebsiteStructureAnalyzer:
    """Parse and extract structured information from HTML"""
    
    @staticmethod
    def extract_forms(html: str) -> List[Dict[str, Any]]:
        """Extract form information from HTML"""
        soup = BeautifulSoup(html, "html.parser")
        forms = []
        
        for form in soup.find_all("form"):
            form_data = {
                "id": form.get("id") or form.get("name") or f"form-{len(forms)}",
                "action": form.get("action", ""),
                "method": form.get("method", "POST").upper(),
                "fields": []
            }
            
            for field in form.find_all(["input", "textarea", "select"]):
                field_info = {
                    "name": field.get("name"),
                    "type": field.get("type", "text"),
                    "id": field.get("id"),
                    "required": field.has_attr("required"),
                    "placeholder": field.get("placeholder"),
                    "pattern": field.get("pattern"),
                    "value": field.get("value")
                }
                form_data["fields"].append(field_info)
            
            # Find submit button
            submit_btn = form.find("button", {"type": "submit"})
            if not submit_btn:
                submit_btn = form.find("input", {"type": "submit"})
            
            if submit_btn:
                form_data["submit_button"] = {
                    "text": submit_btn.get_text(strip=True),
                    "id": submit_btn.get("id")
                }
            
            forms.append(form_data)
        
        return forms
    
    @staticmethod
    def extract_navigation(html: str) -> List[Dict[str, str]]:
        """Extract navigation links"""
        soup = BeautifulSoup(html, "html.parser")
        nav_items = []
        
        # Look for navigation elements
        nav = soup.find("nav") or soup.find("ul", class_=lambda x: x and "nav" in x)
        
        if nav:
            for link in nav.find_all("a"):
                nav_items.append({
                    "text": link.get_text(strip=True),
                    "href": link.get("href", ""),
                    "id": link.get("id")
                })
        
        return nav_items
    
    @staticmethod
    def parse_page(html: str, url: str) -> Dict[str, Any]:
        """Parse complete page structure"""
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract text content
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text(separator=" ", strip=True)
        
        return {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "meta_description": soup.find("meta", attrs={"name": "description"})["content"] if soup.find("meta", attrs={"name": "description"}) else "",
            "forms": WebsiteStructureAnalyzer.extract_forms(html),
            "navigation": WebsiteStructureAnalyzer.extract_navigation(html),
            "text_content": text_content[:2000],  # First 2000 chars
            "headings": [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])],
            "buttons": [
                {
                    "text": btn.get_text(strip=True),
                    "id": btn.get("id"),
                    "class": btn.get("class")
                }
                for btn in soup.find_all("button")
            ]
        }
