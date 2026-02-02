# from typing import List, Literal, Optional
# from langchain_core.pydantic_v1 import BaseModel, Field
# from langchain_core.prompts import ChatPromptTemplate
# from app.services.llm import get_llm
# from app.graph.state import ProjectState
# import json

# class ClassificationOutput(BaseModel):
#     user_level: Literal["beginner", "intermediate", "advanced"] = Field(description="The coding proficiency level of the user")
#     project_type: Literal["web_app", "component", "full_stack"] = Field(description="The type of project requested")
#     complexity: Literal["simple", "medium", "complex"] = Field(description="The complexity of the request")
#     requires_research: bool = Field(description="Whether the request requires external research")
#     tech_stack: List[str] = Field(description="List of technologies to use (e.g. react, tailwind)")
#     extracted_requirements: List[str] = Field(description="List of specific requirements extracted from the prompt")

# async def classifier_agent(state: ProjectState):
#     """
#     Analyzes the user prompt and classifies the request.
#     """
#     prompt = state["original_prompt"]
    
#     llm = get_llm(temperature=0)
#     structured_llm = llm.with_structured_output(ClassificationOutput)
    
#     system_prompt = """You are an expert software architect and project manager. 
#     Analyze the incoming user prompt to determine the user's coding proficiency, project type, complexity, and specific requirements.
    
#     The user wants to build a React application (unless specified otherwise). 
#     If the request is vague or implies a lack of technical detail, classify as 'beginner'.
#     If the request mentions specific libraries, patterns, or architectural constraints, classify as 'intermediate' or 'advanced'.
    
#     'simple' complexity: Basic components, single page, no complex logic.
#     'medium' complexity: Multiple pages, state management, basic API interaction.
#     'complex' complexity: Complex business logic, authentication, real-time features, or obscure domains.
    
#     Set 'requires_research' to True if the request is about a specific domain (e.g. 'barbershop', 'crypto dashboard') where visual or functional inspiration is needed.
#     """
    
#     prompt_template = ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         ("human", "{prompt}")
#     ])
    
#     chain = prompt_template | structured_llm
    
#     result: ClassificationOutput = await chain.ainvoke({"prompt": prompt})
    
#     return {"classification": result.dict()}




from typing import List, Literal, Optional
from langchain_core.pydantic_v1 import BaseModel, Field, validator
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
    
    # CRITICAL FIX: Pydantic v1 validators to handle type coercion
    @validator('requires_research', pre=True)
    def coerce_boolean(cls, v):
        """Convert string booleans to actual booleans"""
        if isinstance(v, str):
            return v.lower().strip() in ('true', '1', 'yes', 't')
        return bool(v) if v is not None else False
    
    @validator('tech_stack', 'extracted_requirements', pre=True)
    def ensure_list(cls, v):
        """Ensure lists are actually lists"""
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v else []
        if isinstance(v, list):
            return v
        try:
            return list(v)
        except:
            return []

async def classifier_agent(state: ProjectState):
    """
    Analyzes the user prompt and classifies the request.
    """
    prompt = state["original_prompt"]
    
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(ClassificationOutput)
    
    # Updated system prompt with explicit type instructions and mobile-first enforcement
    system_prompt = """You are an expert software architect and project manager. 
    Analyze the incoming user prompt to determine the user's coding proficiency, project type, complexity, and specific requirements.
    
    CRITICAL: Return proper types:
    - requires_research: MUST be boolean true or false (NOT string "true" or "false")
    - tech_stack: MUST be array of strings like ["react", "tailwind", "vite"]
    - extracted_requirements: MUST be array of strings
    
    MOBILE-FIRST REQUIREMENT:
    ALL projects are being built for a PHONE IDE and MUST be mobile-first and responsive.
    ALWAYS include "mobile-first responsive design" in extracted_requirements.
    ALWAYS include ["react", "tailwind", "vite"] as the base tech_stack.
    
    The user wants to build a React application (unless specified otherwise). 
    If the request is vague or implies a lack of technical detail, classify as 'beginner'.
    If the request mentions specific libraries, patterns, or architectural constraints, classify as 'intermediate' or 'advanced'.
    
    'simple' complexity: Basic components, single page, no complex logic.
    'medium' complexity: Multiple pages, state management, basic API interaction.
    'complex' complexity: Complex business logic, authentication, real-time features, or obscure domains.
    
    Set 'requires_research' to true (boolean, not string) if the request is about a specific domain (e.g. 'barbershop', 'crypto dashboard') where visual or functional inspiration is needed.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{prompt}")
    ])
    
    chain = prompt_template | structured_llm
    
    try:
        result: ClassificationOutput = await chain.ainvoke({"prompt": prompt})
        
        print(f"✅ Classification successful:")
        print(f"   - User Level: {result.user_level}")
        print(f"   - Project Type: {result.project_type}")
        print(f"   - Complexity: {result.complexity}")
        print(f"   - Requires Research: {result.requires_research} (type: {type(result.requires_research).__name__})")
        print(f"   - Tech Stack: {result.tech_stack}")
        
        return {"classification": result.dict()}
    
    except Exception as e:
        print(f"❌ Classification error: {e}")
        print(f"   Using fallback classification")
        
        # Fallback classification
        return {
            "classification": {
                "user_level": "beginner",
                "project_type": "web_app",
                "complexity": "medium",
                "requires_research": False,  # Boolean!
                "tech_stack": ["react", "tailwind"],
                "extracted_requirements": [prompt[:100]]
            }
        }