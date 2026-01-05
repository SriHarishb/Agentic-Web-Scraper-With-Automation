import json
from typing import Dict, Any
from src.agent.state import WebAutomationState
from src.mcp.tools.browser_tools import BrowserTools
from src.logger import logger

async def execute_action(state: WebAutomationState, tools: BrowserTools) -> Dict[str, Any]:
    """Execution node - executes planned actions"""
    try:
        if "plan" not in state or not state["plan"].get("steps"):
            state["error"] = "No plan available"
            return state
        
        current_step = state.get("current_step", 0)
        steps = state["plan"].get("steps", [])
        
        if current_step >= len(steps):
            state["success"] = True
            return state
        
        step = steps[current_step]
        action = step.get("action", "").lower()
        target = step.get("target")
        data = step.get("data", {}) or {}
        
        logger.info(f"Executing step {current_step + 1}: {action} on {target}")
        
        result = None
        
        if action == "navigate":
            result = await tools.navigate(target)
        
        elif action in ["fill", "fill_form"]:
            # Handle both single value and dict data
            field_data = data
            if "value" in data and len(data) == 1:
                 # Construct dict for fill_form: {selector: value}
                 field_data = {target: data["value"]}
            elif not isinstance(data, dict) or not data:
                 field_data = {target: data}

            # If tools.fill_form expects a form selector + data dict,
            # we should call browser.fill directly if available, OR adapt logic.

            try:
                if hasattr(tools.browser, "fill"):
                    # Direct fill support: selector, value
                    value = data.get("value", "")
                    await tools.browser.fill(target, str(value))
                    result = {"success": True, "page_state": await tools.browser.get_page_state()}
                else:
                    # Fallback to fill_form
                    result = await tools.fill_form(target, field_data)
            except Exception as e:
                 result = {"success": False, "error": str(e)}

        elif action == "click":
            result = await tools.click(target)
        
        elif action == "select":
            result = await tools.select_option(target, data.get("value", ""))
        
        elif action == "submit":
            result = await tools.submit_form(target)
        
        elif action == "wait":
            result = await tools.wait_for(target, int(data.get("timeout", 30000)))
        
        elif action == "extract":
            result = await tools.extract_text(target)
        
        elif action == "screenshot":
            path = f"screenshots/step-{current_step + 1}.png"
            if hasattr(tools.browser, "screenshot"):
                 saved_path = await tools.browser.screenshot(path=path)
                 result = {"success": True, "path": saved_path, "page_state": await tools.browser.get_page_state()}
            else:
                 result = await tools.screenshot()
        
        else:
            result = {"success": False, "error": f"Unknown action: {action}"}
        
        if result and result.get("success"):
            state["browser_state"] = result.get("page_state", {})
            if "path" in result:
                state["screenshots"].append(result["path"])
            logger.info(f"Step {current_step + 1} executed successfully")
        else:
            state["error"] = result.get("error", "Action failed") if result else "No result"
        
        state["agent_reasoning"] = json.dumps(result or {}, default=str)
        return state
        
    except Exception as e:
        logger.error(f"Error in executor: {str(e)}")
        state["error"] = f"Execution failed: {str(e)}"
        return state
