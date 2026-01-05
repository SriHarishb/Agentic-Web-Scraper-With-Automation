from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from src.agent.state import WebAutomationState
from src.agent.nodes.planner import plan_workflow
from src.agent.nodes.executor import execute_action
from src.agent.nodes.validator import validate_step
from src.mcp.tools.browser_tools import BrowserTools
from src.browser.playwright_adapter import PlaywrightAdapter
from src.knowledge_base.retriever import KnowledgeBaseBuilder
from src.config import settings
from src.logger import logger
from typing import Literal
import uuid
from datetime import datetime

class WebAutomationAgent:
    """Main agent orchestrator using LangGraph"""
    
    def __init__(self, kb_builder: KnowledgeBaseBuilder):
        self.llm = ChatOllama(
            model=settings.chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.0  # Zero for consistency
        )
        self.browser = PlaywrightAdapter()
        self.tools = BrowserTools(self.browser)
        self.kb_builder = kb_builder  # Pass KB
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph with recursion protection"""
        graph = StateGraph(WebAutomationState)
        
        # Add nodes
        graph.add_node("plan", self._node_plan)
        graph.add_node("execute", self._node_execute)
        graph.add_node("validate", self._node_validate)
        
        # Add edges
        graph.add_edge("plan", "execute")
        graph.add_edge("execute", "validate")
        
        # Conditional routing
        graph.add_conditional_edges(
            "validate",
            self._should_continue,
            {
                "continue": "execute",
                "done": END
            }
        )
        
        graph.set_entry_point("plan")
        return graph.compile()
    
    async def _node_plan(self, state: WebAutomationState) -> WebAutomationState:
        """Plan with RAG context"""
        return await plan_workflow(state, self.llm)
    
    async def _node_execute(self, state: WebAutomationState) -> WebAutomationState:
        """Execute with browser"""
        return await execute_action(state, self.tools)
    
    async def _node_validate(self, state: WebAutomationState) -> WebAutomationState:
        """Validate with heuristics"""
        return await validate_step(state, self.llm)
    
    def _should_continue(self, state: WebAutomationState) -> Literal["continue", "done"]:
        """Smart routing - prevents recursion"""
        error = state.get("error")
        retries = state.get("retries", 0)

        # If there is a hard error and retries exhausted -> done
        if error and retries >= 2:
            logger.error(f"Stopping after {retries} retries with error: {error}")
            return "done"

        # Check steps completion
        steps = state.get("plan", {}).get("steps", [])
        current_step = state.get("current_step", 0)

        if state.get("success") or current_step >= len(steps):
            state["success"] = True 
            logger.info("Workflow completed successfully")
            return "done"

        # Global step limit safety
        if current_step >= 10: 
            logger.warning("Global step limit reached")
            return "done"

        # If error but retries left, do not replan, just try to continue or fail
        if error:
            state["retries"] = retries + 1
            logger.warning(f"Error encountered but continuing (attempt {retries + 1}): {error}")
            state["error"] = None  # Clear error to avoid immediate stop
            return "continue"

        return "continue"
    
    async def execute_task_with_context(self, task: str, domain: str, kb_builder: KnowledgeBaseBuilder) -> dict:
        """Enhanced execution with RAG context injection"""
        try:
            await self.browser.initialize()
            
            # RAG: Get login context FIRST
            login_context = await kb_builder.search("login form username password")
            logger.info(f"Login selectors found: {len(login_context)} chunks")
            
            # Inject credentials from your history
            form_data = {
                "username": "",
                "password": ""
            }
            
            # Concrete initial state
            state: WebAutomationState = {
                "task": task,
                "domain": domain,
                "retrieved_context": login_context,
                "website_schema": {
                    "login_url": "http://lms2.ai.saveetha.in/login/index.php",
                    "selectors": {
                        "username": "#username",
                        "password": "#password",
                        "loginbtn": "#loginbtn"
                    }
                },
                "form_data": form_data,  
                "plan": {},
                "current_step": 0,
                "steps_completed": [],
                "browser_state": {},
                "success": False,
                "error": None,
                "screenshots": [],
                "agent_reasoning": "",
                "execution_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "retries": 0
            }
            
            logger.info(f"Starting execution: {task}")
            
            # Recursion limit configuration
            config = {"recursion_limit": 15}
            result = await self.graph.ainvoke(state, config)
            
            # Cleanup
            await self.browser.close()
            
            logger.info(f"✓ COMPLETE | Success: {result.get('success')} | Steps: {len(result.get('steps_completed', []))}")
            if result.get("screenshots"):
                logger.info(f"Screenshots: {result['screenshots']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            await self.browser.close()
            return {
                "success": False,
                "error": str(e),
                "execution_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat()
            }
