from typing import TypedDict, List, Dict, Optional, Any, Union
from typing_extensions import Annotated
import operator

class ProjectState(TypedDict):
    """
    Represents the state of the agentic coding workflow.
    """
    # Inputs
    original_prompt: str
    user_id: str
    
    # State
    conversation_history: List[dict]
    current_files: Dict[str, str]  # filename -> content
    user_feedback: Optional[str]
    iteration_count: int
    
    # intermediate outputs
    classification: Optional[dict]
    research_context: Optional[dict]
    design_spec: Optional[dict]
    execution_results: Optional[dict]
    
    # Messages for chat history integration if needed
    # messages: Annotated[List[Any], operator.add]
