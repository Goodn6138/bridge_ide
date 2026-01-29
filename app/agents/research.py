from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from app.services.llm import get_llm
from app.core.config import get_settings
from app.graph.state import ProjectState
import json

settings = get_settings()

async def research_agent(state: ProjectState):
    """
    Performs research on the requested topic.
    """
    classification = state.get("classification", {})
    prompt = state["original_prompt"]
    
    # If no research required, skip? The graph will handle routing, but if we are here, we do research.
    
    llm = get_llm(temperature=0.2)
    
    # Mock search or use Tavily if available (Implementation of actual search omitted for brevity/dependency reasons, focusing on LLM knowledge)
    # framework for search:
    search_context = ""
    if settings.TAVILY_API_KEY:
        # TODO: Implement actual Tavily call
        pass
        
    system_prompt = """You are a Product Researcher.
    Analyze the user's request and provide key insights for building this application.
    Focus on:
    1. Core features expected for this type of application.
    2. Common UI/UX patterns (colors, layout).
    3. Essential data structures.
    
    If the project is a "Barbershop Website", for example, list features like 'Appointment Booking', 'Service Menu', 'Barber Profiles'.
    
    Output a structured summary with 5-10 key insights.
    """
    
    user_prompt = f"""
    User Request: {prompt}
    Project Type: {classification.get('project_type')}
    Context: {classification.get('extracted_requirements')}
    """
    
    messages = [
        ("system", system_prompt),
        ("human", user_prompt)
    ]
    
    response = await llm.ainvoke(messages)
    
    return {"research_context": {"summary": response.content}}
