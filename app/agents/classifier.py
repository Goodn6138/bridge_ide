from typing import List, Literal, Optional
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.services.llm import get_llm
from app.graph.state import ProjectState
import json

class ClassificationOutput(BaseModel):
    user_level: Literal["beginner", "intermediate", "advanced"] = Field(description="The coding proficiency level of the user")
    project_type: Literal["web_app", "component", "full_stack"] = Field(description="The type of project requested")
    complexity: Literal["simple", "medium", "complex"] = Field(description="The complexity of the request")
    requires_research: bool = Field(description="Whether the request requires external research")
    tech_stack: List[str] = Field(description="List of technologies to use (e.g. react, tailwind)")
    extracted_requirements: List[str] = Field(description="List of specific requirements extracted from the prompt")

async def classifier_agent(state: ProjectState):
    """
    Analyzes the user prompt and classifies the request.
    """
    prompt = state["original_prompt"]
    
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(ClassificationOutput)
    
    system_prompt = """You are an expert software architect and project manager. 
    Analyze the incoming user prompt to determine the user's coding proficiency, project type, complexity, and specific requirements.
    
    The user wants to build a React application (unless specified otherwise). 
    If the request is vague or implies a lack of technical detail, classify as 'beginner'.
    If the request mentions specific libraries, patterns, or architectural constraints, classify as 'intermediate' or 'advanced'.
    
    'simple' complexity: Basic components, single page, no complex logic.
    'medium' complexity: Multiple pages, state management, basic API interaction.
    'complex' complexity: Complex business logic, authentication, real-time features, or obscure domains.
    
    Set 'requires_research' to True if the request is about a specific domain (e.g. 'barbershop', 'crypto dashboard') where visual or functional inspiration is needed.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{prompt}")
    ])
    
    chain = prompt_template | structured_llm
    
    result: ClassificationOutput = await chain.ainvoke({"prompt": prompt})
    
    return {"classification": result.dict()}
