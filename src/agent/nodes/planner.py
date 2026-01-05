from langchain_ollama import ChatOllama
from src.agent.state import WebAutomationState
from src.logger import logger
import json
import re

PLANNER_PROMPT = """
You are a smart web automation planner.
TASK: {task}
URL: {domain}

CONTEXT (Scraped HTML):
{retrieved_context}

INSTRUCTIONS:
1. Analyze the CONTEXT to find input names/ids for the task.
2. HackerNews uses name='acct' (user) and name='pw' (pass).
3. Standard sites use name='username', 'email', 'password'.
4. Create a JSON plan.

OUTPUT JSON format:
{{
  "steps": [
    {{ "step": 1, "action": "navigate", "target": "{domain}", "expected_outcome": "Page loaded" }},
    {{ "step": 2, "action": "fill", "target": "SELECTOR", "data": {{ "value": "VALUE" }} }},
    {{ "step": 3, "action": "click", "target": "SELECTOR" }}
  ]
}}
"""

async def plan_workflow(state: WebAutomationState, llm: ChatOllama):
    """Dynamic planning with Smart Fallback"""
    try:
        # 1. Prepare Context
        context = state.get("retrieved_context", [])
        context_str = str(context)[:2000]
        
        # 2. Ask LLM
        prompt = PLANNER_PROMPT.format(
            task=state["task"],
            domain=state["domain"],
            retrieved_context=context_str
        )
        response = await llm.ainvoke(prompt)
        plan_text = response.content.strip()
        
        logger.info(f"Raw LLM Plan: {plan_text[:100]}...") # Debug log
        
        # 3. Parse JSON
        plan_json = extract_json(plan_text)
        
        # 4. SMART FALLBACK (If LLM fails)
        if not plan_json.get("steps"):
            logger.warning("LLM failed. Using Smart Heuristic Fallback.")
            plan_json = generate_heuristic_plan(state["task"], state["domain"])

        state["plan"] = plan_json
        state["current_step"] = 0
        state["steps_completed"] = []
        logger.info(f"Final Plan ({len(plan_json['steps'])} steps): {[s['action'] for s in plan_json['steps']]}")
        return state
        
    except Exception as e:
        logger.error(f"Planner error: {e}")
        # Emergency fallback
        state["plan"] = generate_heuristic_plan(state["task"], state["domain"])
        return state

def generate_heuristic_plan(task: str, domain: str) -> dict:
    """Generates a plan based on task keywords without site-specific hardcoding"""
    steps = [
        {"step": 1, "action": "navigate", "target": domain, "expected_outcome": "Page loaded"}
    ]
    step_count = 2
    task_lower = task.lower()

    # 1. User/Email Field
    # Try generic selectors that work on 90% of sites (including HN 'acct')
    if "user" in task_lower or "login" in task_lower:
        # We try a list of common selectors. The Executor will try them in order if we pass a list, 
        # but here we pick the most likely generic ones.
        # For a truly robust system, Executor should handle list targets.
        # Here we assume standard 'input' but use a broad selector if possible.
        
        # Heuristic: If we don't know the selector, use a common guess list
        # HN uses 'acct', Moodle uses 'username'.
        steps.append({
            "step": step_count,
            "action": "fill", 
            "target": "input[name='acct'], input[name='username'], input[name='email'], #username, #email", 
            "data": {"value": extract_value(task, ["username", "user", "id"])},
            "expected_outcome": "Username filled"
        })
        step_count += 1

    # 2. Password Field
    if "pass" in task_lower:
        steps.append({
            "step": step_count,
            "action": "fill",
            "target": "input[name='pw'], input[name='password'], #password, #pass",
            "data": {"value": extract_value(task, ["password", "pass"])},
            "expected_outcome": "Password filled"
        })
        step_count += 1

    # 3. Submit Button
    steps.append({
        "step": step_count,
        "action": "click",
        "target": "input[type='submit'], button[type='submit'], #loginbtn, button:has-text('Log in'), button:has-text('Sign in')",
        "expected_outcome": "Form submitted"
    })
    step_count += 1

    # 4. Screenshot
    steps.append({
        "step": step_count,
        "action": "screenshot",
        "target": "final_result",
        "expected_outcome": "Evidence captured"
    })

    return {"steps": steps}

def extract_value(text: str, keys: list) -> str:
    """Simple helper to extract 'value' after keyword in task text"""
    # This is a very basic parser. In a real system, use an LLM extractor or strict arguments.
    # Here we just try to return a dummy if we can't find it, or the user should update main.py
    words = text.split()
    for i, word in enumerate(words):
        if any(k in word.lower() for k in keys) and i + 2 < len(words):
            # matches "username is 'bob'" -> returns 'bob'
            val = words[i+2].strip("'").strip('"')
            return val
    return "unknown_value"

def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except:
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
    return {"steps": []}
