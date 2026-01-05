from typing import Dict, Any
import json
import re
from langchain_ollama import ChatOllama 
from src.agent.nodes.planner import extract_json
from src.agent.state import WebAutomationState
from src.logger import logger

VALIDATOR_PROMPT = """
Precise web automation step validator.

Expected Outcome: {expected_outcome}
Page State: {page_state}
Error: {error}

SUCCESS RULES:
- Navigate: Current URL contains "login/index.php"
- Fill: Target field value matches data  
- Click/Submit: Target no longer exists OR page changes
- Post-login: "dashboard", "profile", "welcome", "logout", "student", "courses" OR no "#login"/"#username"
- Screenshot: File saved

Output ONLY JSON:
{{"success": true/false, "reason": "brief", "should_retry": false}}
"""

async def validate_step(state: WebAutomationState, llm: ChatOllama) -> Dict[str, Any]:
    """Validation node - verifies step success with heuristics first"""
    try:
        plan = state.get("plan", {})
        steps = plan.get("steps", [])
        current_step = state.get("current_step", 0)
        
        if current_step >= len(steps):
            state["success"] = True
            logger.info("All steps completed")
            return state
        
        step = steps[current_step]
        expected_outcome = step.get("expected_outcome", "Complete step")
        page_state = state.get("browser_state", {})
        error = state.get("error", "None")
        
        # HEURISTIC VALIDATION FIRST (fast, no LLM)
        validation = validate_heuristic(step, page_state, error, current_step)
        
        # LLM only if heuristic fails
        if not validation.get("success"):
            prompt = VALIDATOR_PROMPT.format(
                expected_outcome=expected_outcome,
                page_state=str(page_state),
                error=error
            )
            response = await llm.ainvoke(prompt)
            validation = extract_json(response.content.strip())
        
        if validation.get("success"):
            state["steps_completed"].append(current_step)
            # Increment step
            state["current_step"] = current_step + 1
            logger.info(f"Step {current_step + 1} validated: {validation.get('reason', 'success')}")
            
            if state["current_step"] >= len(steps):
                state["success"] = True
                logger.info("VALIDATION COMPLETE: All steps finished successfully")
        else:
            logger.warning(f"Step {current_step + 1} failed: {validation.get('reason', 'unknown')}")
            if not validation.get("should_retry", False):
                state["error"] = validation.get('reason', 'Validation failed')
                if current_step < 3:
                    state["current_step"] = current_step + 1
                    state["error"] = None  
        
        return state
        
    except Exception as e:
        logger.error(f"Validator crashed: {str(e)}")
        current_step = state.get("current_step", 0)
        # Auto-advance first 5 steps
        if current_step <= 4:
            state["current_step"] = current_step + 1
            logger.info(f"Auto-advance step {current_step + 1}")
        else:
            state["error"] = f"Validation failed: {str(e)}"
        return state

def validate_heuristic(step: Dict, page_state: Dict, error: str, current_step: int) -> Dict[str, Any]:
    """Fast heuristic validation - no LLM needed"""
    action = step.get("action", "").lower()
    target = step.get("target", "").lower()
    page_content = str(page_state).lower()
    current_url = page_state.get("url", "").lower()
    
    if action == "navigate":
        if "login/index.php" in current_url:
            return {"success": True, "reason": "On login page", "should_retry": False}
    
    elif action == "fill":
        # Success if target selector exists in page content (simpler check)
        clean_target = target.replace("#", "").replace(".", "")
        if clean_target in page_content or target in page_content:
            return {"success": True, "reason": f"Filled {target}", "should_retry": False}
    
    elif action in ["click", "submit"]:
        no_login_form = all(ind not in page_content for ind in ["#login", "#username"])
        page_changed = "login/index.php" not in current_url
        if no_login_form or page_changed:
            return {"success": True, "reason": "Form submitted/page changed", "should_retry": False}
    
    elif action == "screenshot":
        return {"success": True, "reason": "Screenshot completed", "should_retry": False}
    
    # Only check for dashboard success AFTER login click (step 4 onwards)
    if current_step >= 3:
        success_keywords = ["dashboard", "profile", "welcome", "logout", "student", "courses", "saveetha"]
        has_success = any(kw in page_content for kw in success_keywords)
        # S
