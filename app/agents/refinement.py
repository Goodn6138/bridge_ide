from langchain_core.prompts import ChatPromptTemplate
from app.services.llm import get_llm
from app.agents.code_generator import ProjectCode
from app.graph.state import ProjectState
import json

async def refinement_agent(state: ProjectState):
    """
    Refines the code based on user feedback.
    """
    current_files = state.get("current_files")
    feedback = state.get("user_feedback")
    
    if not feedback:
        return {}
        
    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(ProjectCode)
    
    # We only want to enable editing specific files, but for simplicity we re-generate or update.
    # To save tokens, we could first ask what files need changing.
    # For this v1, we'll feed the file list and ask for updates.
    
    system_prompt = """You are an expert React Developer.
    The user wants to modify the existing project.
    
    Current Files:
    {current_files_list}
    
    User Feedback: {feedback}
    
    Return the FULL specifications for ANY file that needs to be changed.
    If a file is unchanged, do not include it in the output (unless necessary for context, but prefer minimal output).
    Actually, to ensure consistency, if a file is heavily dependent, include it.
    BUT, the output MUST contain the full content of the modified files.
    """
    
    # Context compression: passing full code might be too much. 
    # Valid strategy: Pass file names and descriptions/summaries, ask LLM which ones to read, then pass those?
    # For now, simplistic approach: Pass all code (if small) or just filenames.
    # Let's pass all code, assuming < 20k tokens for simple apps.
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Refine the code.")
    ])
    
    files_str = json.dumps(current_files)
    
    result = await structured_llm.ainvoke(prompt_template.format_messages(
        current_files_list=files_str,
        feedback=feedback
    ))
    
    # Merge updates
    updated_files = current_files.copy()
    for f in result.files:
        updated_files[f.filename] = f.content
        
    return {"current_files": updated_files, "iteration_count": state.get("iteration_count", 0) + 1}
