from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from typing import List, Dict
from app.services.llm import get_llm
from app.graph.state import ProjectState

class FileBlueprint(BaseModel):
    filename: str = Field(description="Path and name of the file (e.g. src/components/Header.jsx)")
    description: str = Field(description="Description of what this file contains")
    imports: List[str] = Field(description="Expected imports")

class DesignSpec(BaseModel):
    architecture_overview: str = Field(description="High level explanation of the architecture")
    styling_guide: str = Field(description="Tailwind color palette and design tokens to use")
    component_hierarchy: str = Field(description="Tree structure of components")
    file_structure: List[FileBlueprint] = Field(description="List of files to generate")

async def design_agent(state: ProjectState):
    """
    Plans the architecture and file structure.
    """
    classification = state.get("classification")
    research = state.get("research_context", {})
    prompt = state["original_prompt"]
    
    llm = get_llm(temperature=0.2)
    # Use json_schema method to avoid Groq function/tool calling behavior
    structured_llm = llm.with_structured_output(DesignSpec, method="json_schema")
    
    system_prompt = """You are a Senior React Architect specializing in MOBILE-FIRST design.
    Based on the requirements and research, design a robust React application structure optimized for PHONE IDE.
    
    MOBILE-FIRST DESIGN PRINCIPLES:
    - Design for mobile screens FIRST (320px-428px width)
    - Scale up to tablet (768px) and desktop (1024px+)
    - Use touch-friendly component sizes (min 44px tap targets)
    - Prioritize vertical scrolling over horizontal
    - Use responsive typography (text-sm md:text-base lg:text-lg)
    - Implement mobile-optimized navigation (hamburger menus, bottom nav bars)
    
    RESPONSIVE STRATEGY:
    - Start with mobile layout (no prefix)
    - Add tablet adjustments (md: prefix)
    - Add desktop enhancements (lg: prefix)
    - Example: className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
    
    STYLING REQUIREMENTS:
    - Use Tailwind CSS exclusively
    - Responsive containers: "container mx-auto px-4"
    - Full viewport layouts: "min-h-screen"
    - Touch-friendly buttons: "min-h-[44px] px-6 py-3"
    - Readable mobile text: minimum text-base (16px)
    
    PROJECT STRUCTURE:
    - src/components/ (Atomic or module based, mobile-first)
    - src/pages/ (if routing needed)
    - src/App.jsx (Main entry with mobile layout)
    - src/index.css (Global styles, tailwind directives)
    - package.json
    - postcss.config.js
    - tailwind.config.js
    - index.html (MUST include viewport meta tag)
    
    Provide a complete file list so the Code Generator knows exactly what to build.
    Ensure all components are designed mobile-first with responsive breakpoints.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Request: {prompt}\nResearch: {research}\nClassification: {classification}")
    ])
    
    chain = prompt_template | structured_llm
    
    result = await chain.ainvoke({
        "prompt": prompt,
        "research": research.get("summary", "None"),
        "classification": classification
    })
    
    return {"design_spec": result.dict()}
