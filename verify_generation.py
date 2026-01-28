import asyncio
import json
from app.graph.workflow import define_graph
from app.core.config import get_settings

async def main():
    settings = get_settings()
    if not settings.GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set.")
        return

    print("--- Starting Verification ---")
    
    # Test Prompt
    prompt = "Create a simple React counter component with increment and decrement buttons."
    print(f"Prompt: {prompt}")
    
    initial_state = {
        "original_prompt": prompt,
        "user_id": "test_verification",
        "conversation_history": [],
        "iteration_count": 0,
        "current_files": {},
        "user_feedback": None
    }
    
    graph = define_graph()
    
    async for event in graph.astream(initial_state):
        for key, value in event.items():
            print(f"\n[Node Completed]: {key}")
            
            if key == "classifier":
                print(f"Classification: {json.dumps(value.get('classification'), indent=2)}")
            
            elif key == "design":
                print("Design Specs Generated.")
                specs = value.get('design_spec', {})
                
                # Handle file_structure which can be list of dicts or objects
                file_structure = specs.get('file_structure', [])
                if file_structure:
                    try:
                        # Check if it's a list of dicts
                        if isinstance(file_structure[0], dict):
                            filenames = [
                                f.get('filename') or f.get('path') or f.get('name') or 'unknown' 
                                for f in file_structure
                            ]
                            print(f"Proposed Files ({len(filenames)}): {filenames}")
                        # Otherwise it's an object with .filename attribute
                        else:
                            filenames = [f.filename for f in file_structure]
                            print(f"Proposed Files ({len(filenames)}): {filenames}")
                    except (IndexError, AttributeError, KeyError) as e:
                        print(f"⚠️  Could not parse file structure: {e}")
                        print(f"    Format: {type(file_structure[0]) if file_structure else 'empty'}")
                        # Print the raw structure for debugging
                        print(f"    Raw: {json.dumps(file_structure[:2], indent=2, default=str)}")
                else:
                    print("⚠️  No file structure found in design specs")
                
                # Optionally print full design specs for debugging
                # print(f"\nFull Design Specs:\n{json.dumps(specs, indent=2, default=str)}")
            
            elif key == "code_generator":
                files = value.get("current_files", {})
                print(f"✅ Generated {len(files)} files:")
                for fname in sorted(files.keys()):
                    file_size = len(files[fname])
                    print(f"   📄 {fname} ({file_size:,} bytes)")
                    
                    # Print a small snippet of each file
                    if file_size > 0:
                        snippet = files[fname][:150].replace('\n', ' ')
                        print(f"      Preview: {snippet}...")
                
                # Save files to disk for inspection
                import os
                output_dir = "test_verification_output"
                os.makedirs(output_dir, exist_ok=True)
                
                for fname, content in files.items():
                    filepath = os.path.join(output_dir, fname)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                print(f"\n💾 All files saved to '{output_dir}/' directory")
            
            elif key == "research":
                research = value.get('research_context')
                if research:
                    insights = research.get('insights', [])
                    print(f"Research: {len(insights)} insights gathered")
                    for i, insight in enumerate(insights[:3], 1):
                        print(f"  {i}. {insight[:80]}...")
                else:
                    print("Research: Skipped (not required)")

    print("\n" + "="*80)
    print("✅ Verification Complete!")
    print("="*80)
    print("\nYour agents are working! 🎉")
    print("Check the 'test_verification_output' folder for generated files.")

if __name__ == "__main__":
    asyncio.run(main())