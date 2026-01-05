from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict

class WebAutomationState(TypedDict, total=False):
    """Shared state for LangGraph agent"""
    
    # Task Definition
    task: str
    domain: str
    
    # Knowledge Base Context
    retrieved_context: List[str]
    website_schema: Dict[str, Any]
    
    # Planning
    plan: Dict[str, Any]
    current_step: int
    steps_completed: List[str]
    
    # Execution State
    browser_state: Dict[str, Any]
    form_data: Dict[str, str]
    
    # Results
    success: bool
    error: Optional[str]
    screenshots: List[str]
    
    # Reasoning
    agent_reasoning: str
    
    # Metadata
    execution_id: str
    timestamp: str
    retries: int
