from langgraph.graph import StateGraph, END
from app.graph.state import ProjectState
from app.agents.classifier import classifier_agent
from app.agents.research import research_agent
from app.agents.design import design_agent
from app.agents.code_generator import code_generator_agent
from app.agents.file_organizer import file_organizer_agent
from app.agents.qa import qa_agent
from app.agents.refinement import refinement_agent

async def router_node(state: ProjectState):
    """
    Routes to the appropriate starting point.
    """
    # This node doesn't modify state, just exists for routing
    return {}

def define_graph():
    workflow = StateGraph(ProjectState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("classifier", classifier_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("design", design_agent)
    workflow.add_node("code_generator", code_generator_agent)
    workflow.add_node("file_organizer", file_organizer_agent)
    workflow.add_node("qa", qa_agent)
    workflow.add_node("refinement", refinement_agent)
    
    workflow.set_entry_point("router")
    
    # Dynamic Routing from start
    def route_start(state):
        if state.get("user_feedback"):
            return "refinement"
        return "classifier"

    workflow.add_conditional_edges(
        "router",
        route_start,
        {
            "refinement": "refinement",
            "classifier": "classifier"
        }
    )

    # Classifier Routing
    def route_classifier(state):
        classification = state.get("classification", {})
        user_level = classification.get("user_level")
        complexity = classification.get("complexity")
        
        if user_level == "beginner" or complexity == "complex":
            return "research"
        else:
            return "code_generator"
            
    workflow.add_conditional_edges(
        "classifier",
        route_classifier,
        {
            "research": "research",
            "code_generator": "code_generator"
        }
    )
    
    # Research -> Design -> Code Gen
    workflow.add_edge("research", "design")
    workflow.add_edge("design", "code_generator")
    
    # Code Gen -> File Organizer -> QA -> End
    workflow.add_edge("code_generator", "file_organizer")
    workflow.add_edge("file_organizer", "qa")
    workflow.add_edge("qa", END)
    
    # Refinement -> File Organizer
    workflow.add_edge("refinement", "file_organizer")
    
    return workflow.compile()
