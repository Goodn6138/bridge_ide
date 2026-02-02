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
    
    # ✅ MOBILE-FIRST: Enhanced prompt for phone IDE
    system_prompt = """You are an Expert React Developer specializing in MOBILE-FIRST applications.
    Generate strictly working code for a PHONE IDE environment.
    
    Technology Stack: React, Tailwind CSS, Vite
    
    CRITICAL MOBILE-FIRST REQUIREMENTS:
    1. ALL components MUST use mobile-first Tailwind classes
    2. Start with mobile layout (no prefix), then add md: and lg: breakpoints
    3. Use responsive patterns:
       - Typography: "text-sm md:text-base lg:text-lg"
       - Spacing: "p-4 md:p-6 lg:p-8"
       - Grid: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
       - Flex: "flex-col md:flex-row"
    4. Touch-friendly sizing: buttons min-h-[44px], tap targets min 44px
    5. Readable mobile text: minimum text-base (16px)
    6. Full viewport: use "min-h-screen" for main containers
    7. Mobile padding: use "px-4" or "container mx-auto px-4"
    
    Project Structure Requirements:
    1. Output VALID, COMPLETE code for every file - NO placeholders
    2. File specifications:
       - `package.json`: "type": "module", dependencies: react, react-dom, vite, @vitejs/plugin-react, tailwindcss, autoprefixer, postcss
       - `vite.config.js`: use `export default defineConfig({{{{ plugins: [...] }}}})``
       - `postcss.config.js`: use `export default {{{{ plugins: {{{{ tailwindcss: {{}}, autoprefixer: {{}} }}}} }}}}` (ESM syntax)
       - `tailwind.config.js`: use `export default {{{{ content: [...], theme: {{{{ extend: {{}} }}}}, plugins: [] }}}}` (ESM syntax)
       - `index.html`: 
         * MUST include: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
         * Element with id="root"
         * Script type="module" src="/src/main.jsx"
       - `src/index.css`: `@tailwind base; @tailwind components; @tailwind utilities;`
       - `src/main.jsx`: 
         * Must `import './index.css'`
         * Render App component to root
       - `src/App.jsx`:
         * Use "min-h-screen" for full viewport
         * Use "container mx-auto px-4" for mobile padding
         * Mobile-first responsive layout
    
    COMPONENT STYLING RULES:
    - Every component MUST use Tailwind classes
    - Start mobile-first: "w-full md:w-1/2 lg:w-1/3"
    - Responsive containers: "max-w-7xl mx-auto px-4"
    - Touch-friendly: "py-3 px-6 min-h-[44px]" for buttons
    - Proper spacing: "space-y-4 md:space-y-6"
    
    Files to generate: {file_list}
    
    Ensure all components export correctly, import correctly, and use mobile-first responsive Tailwind patterns.
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
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
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
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        // Suppress unresolved import warnings - treat as external
        if (warning.code === 'UNRESOLVED_IMPORT') return;
        warn(warning);
      }
    }
  }
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-6 md:py-8 lg:py-12">
        {component_jsx}
      </div>
    </div>
  );
}}

export default App;
"""
    
    # Generate component files with mobile-first styling
    for comp in components:
        files[f"src/components/{comp}.jsx"] = f"""import React from 'react';

function {comp}() {{
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-xl shadow-2xl p-4 md:p-6 lg:p-8 mb-4 md:mb-6">
      <h2 className="text-xl md:text-2xl lg:text-3xl font-bold text-orange-400 mb-3 md:mb-4">{comp}</h2>
      <p className="text-base md:text-lg text-gray-300 leading-relaxed">This is the {comp} component.</p>
      <button className="mt-4 bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-6 rounded-lg min-h-[44px] transition-colors duration-200">
        Learn More
      </button>
    </div>
  );
}}

export default {comp};
"""
    
    return files


async def build_react_app(project_id: str, app_id: str, files: Dict[str, str]) -> Dict[str, any]:
    """
    Build React app by writing files to disk and running npm locally.
    On Vercel, npm is not available at runtime - gracefully degrades to StackBlitz preview.
    
    Args:
        project_id: Internal project ID for tracking
        app_id: Public app ID for preview naming
        files: Dict of filename -> content for the React project
    
    Returns:
        Dict with build_success, dist_url/preview_url, error_message
    """
    import subprocess
    from pathlib import Path
    import shutil
    
    try:
        print(f"📦 Building React app for {app_id}...")
        
        # Check if npm is available
        npm_available = False
        try:
            result = subprocess.run(
                "npm --version",
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            npm_available = result.returncode == 0
        except Exception:
            npm_available = False
        
        if not npm_available:
            # npm not available (Vercel production) - save files for StackBlitz preview
            print(f"   ⚠️ npm not available (Vercel serverless) - saving files for StackBlitz preview")
            
            # Save files to a temporary location so they can be served
            preview_dir = Path(f"/tmp/previews/{app_id}/stackblitz")
            preview_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, content in files.items():
                filepath = preview_dir / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_text(content)
            
            # Return a URL to the StackBlitz preview page that will be served by preview route
            return {
                "build_success": True,
                "build_output": "Using StackBlitz preview (npm not available in serverless)",
                "error_message": None,
                "dist_url": f"/api/preview/stackblitz/{app_id}",
                "preview_method": "stackblitz"
            }
        
        # npm is available - proceed with local build
        
        # Create project directory (use /tmp for Vercel serverless)
        project_dir = Path(f"/tmp/previews/{app_id}/build")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Write all files to disk
        for filename, content in files.items():
            filepath = project_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)
        
        print(f"   ✓ Wrote {len(files)} files to {project_dir}")
        
        # Modify vite.config.js to include correct base path
        vite_config_path = project_dir / "vite.config.js"
        if vite_config_path.exists():
            vite_content = vite_config_path.read_text()
            # Inject base path into the config
            base_path = f"/preview/{app_id}/dist/"
            vite_content = vite_content.replace(
                "export default defineConfig({",
                f"export default defineConfig({{\n  base: '{base_path}',"
            )
            vite_config_path.write_text(vite_content)
            print(f"   ✓ Set vite base path to {base_path}")

        
        # Run npm install
        print(f"   → npm install...")
        result = subprocess.run(
            "npm install --legacy-peer-deps",
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
            shell=True
        )
        
        if result.returncode != 0:
            error = result.stderr or result.stdout
            print(f"   ❌ npm install failed: {error}")
            return {
                "build_success": False,
                "build_output": result.stdout + result.stderr,
                "error_message": f"npm install failed: {error}",
                "dist_url": None
            }
        
        print(f"   ✓ npm install complete")
        
        # Run npm build
        print(f"   → npm run build...")
        result = subprocess.run(
            "npm run build",
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
            shell=True
        )
        
        if result.returncode != 0:
            error = result.stderr or result.stdout
            print(f"   ❌ npm run build failed: {error}")
            return {
                "build_success": False,
                "build_output": result.stdout + result.stderr,
                "error_message": f"npm build failed: {error}",
                "dist_url": None
            }
        
        print(f"   ✓ npm build complete")
        
        # Check if dist directory exists
        dist_dir = project_dir / "dist"
        if not dist_dir.exists():
            return {
                "build_success": False,
                "error_message": "Build completed but dist/ directory not found",
                "build_output": result.stdout,
                "dist_url": None
            }
        
        # Move dist to preview directory (for serving)
        preview_dist = Path(f"/tmp/previews/{app_id}/dist")
        if preview_dist.exists():
            shutil.rmtree(preview_dist)
        shutil.move(str(dist_dir), str(preview_dist))
        
        # Cleanup build artifacts
        shutil.rmtree(project_dir)
        
        print(f"✅ Build successful for {app_id}")
        
        return {
            "build_success": True,
            "build_output": result.stdout,
            "error_message": None,
            "dist_url": f"/preview/{app_id}/dist/index.html",
            "preview_method": "local"
        }
    
    except subprocess.TimeoutExpired:
        print(f"❌ Build timeout (exceeded 120s)")
        return {
            "build_success": False,
            "build_output": "",
            "error_message": "Build timeout - npm install or build took too long",
            "dist_url": None
        }
    
    except Exception as e:
        print(f"❌ Build error: {e}")
        return {
            "build_success": False,
            "build_output": str(e),
            "error_message": str(e),
            "dist_url": None
        }


def generate_stackblitz_url(app_id: str, files: Dict[str, str]) -> str:
    """
    Generate an HTML page that creates a StackBlitz project with auto-submit form.
    StackBlitz doesn't allow direct URL-based project creation without a backend,
    so we return HTML that posts the files to StackBlitz's API.
    
    Args:
        app_id: Project ID
        files: Generated file contents
    
    Returns:
        HTML content with auto-submitting form to StackBlitz
    """
    import json
    
    # Prepare files for StackBlitz format
    # StackBlitz expects files in format: "filename" -> "content"
    stackblitz_files = {}
    for filename, content in files.items():
        stackblitz_files[filename] = content
    
    # Create the project data payload
    project_data = {
        "files": stackblitz_files,
        "template": "node",
        "title": f"Bridge IDE - {app_id}",
        "description": "Generated React App Preview"
    }
    
    # Generate HTML with auto-submitting form
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Opening Preview...</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }}
            .container {{
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
            }}
            p {{
                color: #666;
                margin: 10px 0;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .button {{
                background: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }}
            .button:hover {{
                background: #2980b9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Opening Preview...</h1>
            <p>Creating your React app preview on StackBlitz</p>
            <div class="spinner"></div>
            <p>If the page doesn't open automatically, click the button below:</p>
            <form id="stackblitz-form" method="post" action="https://stackblitz.com/api/v1/project" target="_blank">
                <button type="submit" class="button">Open on StackBlitz</button>
            </form>
        </div>
        
        <script>
            // Prepare the project data
            const projectData = {json.dumps(project_data)};
            
            // Set form fields for each file
            const form = document.getElementById('stackblitz-form');
            
            Object.entries(projectData.files).forEach(([filename, content]) => {{
                const input = document.createElement('textarea');
                input.name = 'files[' + filename + ']';
                input.value = content;
                form.appendChild(input);
            }});
            
            // Add other project settings
            const titleInput = document.createElement('input');
            titleInput.type = 'hidden';
            titleInput.name = 'title';
            titleInput.value = projectData.title;
            form.appendChild(titleInput);
            
            const templateInput = document.createElement('input');
            templateInput.type = 'hidden';
            templateInput.name = 'template';
            templateInput.value = projectData.template;
            form.appendChild(templateInput);
            
            const descInput = document.createElement('input');
            descInput.type = 'hidden';
            descInput.name = 'description';
            descInput.value = projectData.description;
            form.appendChild(descInput);
            
            // Auto-submit the form after a short delay
            setTimeout(() => {{
                form.submit();
            }}, 500);
        </script>
    </body>
    </html>
    """
    
    return html_content
