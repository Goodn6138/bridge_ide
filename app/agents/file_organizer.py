from app.graph.state import ProjectState
from app.services.llm import get_llm

async def file_organizer_agent(state: ProjectState):
    """
    Ensures all necessary files are present and properly structured.
    """
    files = state.get("current_files", {}).copy()
    
    # 1. Check for package.json
    has_package_json = any("package.json" in k for k in files)
    
    # 2. Check for entry point (index.html for Vite)
    has_index_html = any("index.html" in k for k in files)
    
    # 3. Add default defaults if missing (using a simple heuristic or LLM if strictly needed, keeping it simple here)
    if not has_package_json:
        files["package.json"] = """{
  "name": "generated-project",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "vite": "^5.0.8"
  }
}"""

    if not has_index_html:
         files["index.html"] = """<!doctype html>
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
</html>"""

    # Ensure src/main.jsx (or index.jsx) exists if index.html points to it
    # This is a bit complex to valid statically without parsing HTML, 
    # but we assume CodeGenerator did a decent job.
    
    # Add .gitignore
    if ".gitignore" not in files:
        files[".gitignore"] = "node_modules\ndist\n.env\n"
    
    # Add vite.config.js if missing (required for React + Vite)
    if "vite.config.js" not in files:
        files["vite.config.js"] = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      onwarn(warning, warn) {
        // Suppress unresolved import warnings - treat as external
        if (warning.code === 'UNRESOLVED_IMPORT') return;
        warn(warning);
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  }
})"""
    
    # Add postcss.config.js for Tailwind CSS
    if "postcss.config.js" not in files:
        files["postcss.config.js"] = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
    
    # Add tailwind.config.js
    if "tailwind.config.js" not in files:
        files["tailwind.config.js"] = """export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
        
    return {"current_files": files}
