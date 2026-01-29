# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.pydantic_v1 import BaseModel, Field
# from typing import List, Dict
# from app.services.llm import get_llm
# from app.graph.state import ProjectState
# import json

# class CodeFile(BaseModel):
#     filename: str = Field(description="The path and filename")
#     content: str = Field(description="The complete code content")

# class ProjectCode(BaseModel):
#     files: List[CodeFile] = Field(description="List of all generated files")

# async def code_generator_agent(state: ProjectState):
#     """
#     Generates the actual code for the project.
#     """
#     design_spec = state.get("design_spec")
#     classification = state.get("classification")
    
#     # If no design spec (simple path), we might generate on the fly, but for now assuming Design Agent ran.
#     # If Design Agent didn't run (Experienced path), we simulate design or just ask for code directly.
    
#     file_list = []
#     if design_spec:
#         # ✅ REPLACE LINE 27 WITH THIS:
#         file_structure = design_spec.get('file_structure', [])
#         if file_structure and isinstance(file_structure[0], dict):
#             # It's a list of dicts - use .get()
#             file_list = [f.get('filename') or f.get('path') for f in file_structure]
#         else:
#             # It's a list of objects - use .filename
#             file_list = [f.filename for f in file_structure]
        
#     llm = get_llm(temperature=0.1) # Low temp for code
#     # context window management: if too many files, might need multiple calls.
#     # For now, we attempt single pass for typical "demo" size apps.
    
#     structured_llm = llm.with_structured_output(ProjectCode)
    
#     system_prompt = """You are an Expert React Developer.
#     Generate the strictly working code for the requested project.
    
#     Technology Stack: React, Tailwind CSS (via CDN or standard config), Vite (implied structure).
    
#     Requirements:
#     1. Output VALID code for every file.
#     2. Ensure NO placeholders.
#     3. Project Structure:
#        - `package.json`: keys "type": "module", dependencies: react, react-dom, vite, @vitejs/plugin-react, tailwindcss, autoprefixer, postcss.
#        - `vite.config.js`: use `export default defineConfig({ ... })`.
#        - `postcss.config.js`: use `export default { plugins: { ... } }` (ESM syntax).
#        - `tailwind.config.js`: use `export default { ... }` (ESM syntax).
#        - `index.html`: element with id="root", script type="module" src="/src/main.jsx".
#        - `src/index.css`: `@tailwind base; @tailwind components; @tailwind utilities;`.
#        - `src/main.jsx`: 
#          - Must `import './index.css'` (or appropriate CSS path).
#          - Render App component to root.

#     Files to generate:
#     {file_list}
    
#     Make sure components export correctly and import correctly.
#     """
    
#     prompt_template = ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         ("human", "Design Spec: {design_spec}\n\nGenerate the code.")
#     ])
    
#     chain = prompt_template | structured_llm
    
#     input_data = {
#         "file_list": ", ".join(file_list) if file_list else "Standard React App structure",
#         "design_spec": json.dumps(design_spec) if design_spec else "Create a standard robust app."
#     }
    
#     result = await chain.ainvoke(input_data)
    
#     current_files = {f.filename: f.content for f in result.files}
    
#     return {"current_files": current_files}



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
        # ✅ FIXED: Handle file_structure as dicts or objects
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
    
    # ✅ FIXED: Escaped all { } that aren't template variables
    system_prompt = """You are an Expert React Developer.
    Generate the strictly working code for the requested project.
    
    Technology Stack: React, Tailwind CSS (via CDN or standard config), Vite (implied structure).
    
    Requirements:
    1. Output VALID code for every file.
    2. Ensure NO placeholders.
    3. Project Structure:
       - `package.json`: keys "type": "module", dependencies: react, react-dom, vite, @vitejs/plugin-react, tailwindcss, autoprefixer, postcss.
       - `vite.config.js`: use `export default defineConfig({{{{ plugins: [...] }}}})`.
       - `postcss.config.js`: use `export default {{{{ plugins: {{{{ tailwindcss: {{}}, autoprefixer: {{}} }}}} }}}}` (ESM syntax).
       - `tailwind.config.js`: use `export default {{{{ content: [...], theme: {{{{ extend: {{}} }}}}, plugins: [] }}}}` (ESM syntax).
       - `index.html`: element with id="root", script type="module" src="/src/main.jsx".
       - `src/index.css`: `@tailwind base; @tailwind components; @tailwind utilities;`.
       - `src/main.jsx`: 
         - Must `import './index.css'` (or appropriate CSS path).
         - Render App component to root.

    Files to generate: {file_list}
    
    Make sure components export correctly and import correctly.
    Use Tailwind CSS classes for all styling.
    Include proper imports and exports.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Design Spec: {design_spec}\n\nGenerate complete, working code for all files.")
    ])
    
    chain = prompt_template | structured_llm
    
    # ✅ Prepare input data with all required variables
    input_data = {
        "file_list": ", ".join(file_list) if file_list else "Standard React App structure",
        "design_spec": json.dumps(design_spec) if design_spec else "Create a standard robust app."
    }
    
    print(f"🔨 Generating code for {len(file_list)} files...")
    
    try:
        result = await chain.ainvoke(input_data)
        
        current_files = {f.filename: f.content for f in result.files}
        
        print(f"✅ Generated {len(current_files)} files:")
        for filename in sorted(current_files.keys()):
            print(f"   📄 {filename} ({len(current_files[filename])} bytes)")
        
        return {"current_files": current_files}
    
    except Exception as e:
        print(f"❌ Code generation error: {e}")
        print(f"   Attempting fallback generation...")
        
        # Fallback: generate basic structure
        fallback_files = generate_fallback_files(file_list, design_spec)
        return {"current_files": fallback_files}


def generate_fallback_files(file_list: List[str], design_spec: dict) -> Dict[str, str]:
    """Generate basic fallback files if LLM fails"""
    
    files = {}
    
    # package.json
    files["package.json"] = """{
  "name": "generated-react-app",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}"""
    
    # vite.config.js
    files["vite.config.js"] = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
"""
    
    # tailwind.config.js
    files["tailwind.config.js"] = """export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
    
    # postcss.config.js
    files["postcss.config.js"] = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
    
    # src/index.css
    files["src/index.css"] = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
    
    # index.html
    files["index.html"] = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Generated App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""
    
    # src/main.jsx
    files["src/main.jsx"] = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
    
    # src/App.jsx
    components = design_spec.get('components', ['Main']) if design_spec else ['Main']
    component_imports = '\n'.join([f"import {comp} from './components/{comp}.jsx';" for comp in components])
    component_jsx = '\n      '.join([f"<{comp} />" for comp in components])
    
    files["src/App.jsx"] = f"""import React from 'react';
{component_imports}

function App() {{
  return (
    <div className="min-h-screen bg-gray-900">
      <div className="container mx-auto py-8">
        {component_jsx}
      </div>
    </div>
  );
}}

export default App;
"""
    
    # Generate component files
    for comp in components:
        files[f"src/components/{comp}.jsx"] = f"""import React from 'react';

function {comp}() {{
  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-orange-500 mb-4">{comp}</h2>
      <p className="text-gray-300">This is the {comp} component.</p>
    </div>
  );
}}

export default {comp};
"""
    
    return files