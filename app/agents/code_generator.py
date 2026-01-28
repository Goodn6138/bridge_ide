from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict
from app.services.llm import get_llm
from app.graph.state import ProjectState
import json

class CodeFile(BaseModel):
    filename: str = Field(description="The path and filename")
    content: str = Field(description="The complete code content")

class ProjectCode(BaseModel):
    files: List[CodeFile] = Field(description="List of all generated files")

async def code_generator_agent(state: ProjectState):
    """
    Generates the actual code for the project.
    """
    design_spec = state.get("design_spec")
    classification = state.get("classification")
    
    # If no design spec (simple path), we might generate on the fly, but for now assuming Design Agent ran.
    # If Design Agent didn't run (Experienced path), we simulate design or just ask for code directly.
    
    file_list = []
    if design_spec:
        # ✅ REPLACE LINE 27 WITH THIS:
        file_structure = design_spec.get('file_structure', [])
        if file_structure and isinstance(file_structure[0], dict):
            # It's a list of dicts - use .get()
            file_list = [f.get('filename') or f.get('path') for f in file_structure]
        else:
            # It's a list of objects - use .filename
            file_list = [f.filename for f in file_structure]
        
    llm = get_llm(temperature=0.1) # Low temp for code
    # context window management: if too many files, might need multiple calls.
    # For now, we attempt single pass for typical "demo" size apps.
    
    structured_llm = llm.with_structured_output(ProjectCode)
    
    system_prompt = """You are an Expert React Developer.
    Generate the strictly working code for the requested project.
    
    Technology Stack: React, Tailwind CSS (via CDN or standard config), Vite (implied structure).
    
    Requirements:
    1. Output VALID code for every file.
    2. Ensure NO placeholders.
    3. Include `package.json` with `react`, `react-dom`, `vite`, `tailwindcss`, `autoprefixer`, `postcss`.
    4. Include `vite.config.js`.
    5. Include `tailwind.config.js` and `postcss.config.js`.
    6. Include `index.html` with root div.
    
    Files to generate:
    {file_list}
    
    Make sure components export correctly and import correctly.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Design Spec: {design_spec}\n\nGenerate the code.")
    ])
    
    chain = prompt_template | structured_llm
    
    input_data = {
        "file_list": ", ".join(file_list) if file_list else "Standard React App structure",
        "design_spec": json.dumps(design_spec) if design_spec else "Create a standard robust app."
    }
    
    result = await chain.ainvoke(input_data)
    
    current_files = {f.filename: f.content for f in result.files}
    
    return {"current_files": current_files}
