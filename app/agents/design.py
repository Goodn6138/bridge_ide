from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
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
    structured_llm = llm.with_structured_output(DesignSpec)
    
    system_prompt = """You are a Senior React Architect.
    Based on the requirements and research, design a robust React application structure.
    
    Rules:
    - Use Functional Components with Hooks.
    - Use Tailwind CSS for styling.
    - Structure strictly:
      - src/components/ (Atomic or module based)
      - src/pages/ (if routing needed)
      - src/App.jsx (Main entry)
      - src/index.css (Global styles, tailwind directives)
      - package.json
      - postcss.config.js
      - tailwind.config.js
    
    Provide a complete file list so the Code Generator knows exactly what to build.
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
