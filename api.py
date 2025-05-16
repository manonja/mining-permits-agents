from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
import uvicorn
from typing import Optional, List, Dict

# Import your mining agents
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.mining_agents.crew import MiningAgents

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

app = FastAPI(title="Mining Agents API")

# Add CORS middleware to allow Retool to call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the input model
class ProjectInput(BaseModel):
    project_name: str
    location_region: str
    cobalt_type: str
    scale: str

class NextStep(BaseModel):
    step: str
    explanation: str

class EAResponse(BaseModel):
    project_parameters: dict
    regulatory_check: Optional[str] = None 
    pd_outline: Optional[dict] = None
    indigenous_nations: Optional[str] = None
    next_steps: Optional[List[NextStep]] = None

# Add a root route for testing
@app.get("/")
async def root():
    return {"status": "Mining Agents API is running"}

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/run-ea-scoping", response_model=EAResponse)
async def run_ea_scoping(input_data: ProjectInput):
    """Run the EA scoping process with the mining agents"""
    try:
        # Prepare inputs for CrewAI
        inputs = {
            'project_name': input_data.project_name,
            'location_region': input_data.location_region,
            'cobalt_type': input_data.cobalt_type,
            'scale': input_data.scale
        }
        
        # Save inputs to file for reference
        with open('output/user_inputs.json', 'w') as f:
            json.dump(inputs, f, indent=2)
        
        # Run the Crew
        result = MiningAgents().crew().kickoff(inputs=inputs)
        
        # Read output files for response
        response_data = {
            "project_parameters": inputs
        }
        
        # Read regulatory check results if file exists
        try:
            if os.path.exists('output/regulatory_check.md'):
                with open('output/regulatory_check.md', 'r') as f:
                    regulatory_content = f.read()
                    # Ensure proper Markdown formatting
                    regulatory_content = regulatory_content.replace('\n\n', '\n')
                    # Make sure bullet points are properly formatted
                    regulatory_content = regulatory_content.replace('*   ', '* ')
                    response_data["regulatory_check"] = regulatory_content
        except Exception as e:
            print(f"Error reading regulatory_check.md: {e}")
        
        # Read project description outline if file exists
        try:
            if os.path.exists('output/pd_outline.md'):
                with open('output/pd_outline.md', 'r') as f:
                    pd_content = f.read()
                    
                    # Initialize a dictionary for the two main sections
                    sections = {}
                    
                    import re
                    
                    # Find main section blocks (includes header and all content until next main section)
                    main_section_pattern = r'\*\*(Project Overview|Potential Environmental Effects)\*\*(.*?)(?=\*\*(Project Overview|Potential Environmental Effects)\*\*|\Z)'
                    main_sections = re.findall(main_section_pattern, pd_content, re.DOTALL)
                    
                    for section_match in main_sections:
                        section_name = section_match[0].strip()
                        section_content = section_match[1].strip()
                        
                        # Transform subsection headers format to what we want
                        # Change: * **Subsection:** content
                        # To: * Subsection: content
                        section_content = re.sub(r'\*\s+\*\*(.*?):\*\*', r'* \1:', section_content)
                        
                        # Extract all bullet points with their content, preserving original formatting
                        bullet_points = re.findall(r'(\*\s+.*?)(?=\*\s+|$)', section_content, re.DOTALL)
                        
                        # Combine all bullet points into a single string
                        if bullet_points:
                            # Join all bullet points with newlines
                            combined_content = "\n".join([bp.strip() for bp in bullet_points])
                            sections[section_name] = combined_content
                    
                    response_data["pd_outline"] = sections
        except Exception as e:
            print(f"Error reading pd_outline.md: {e}")
            import traceback
            print(traceback.format_exc())
            
        # Read indigenous nations info if file exists
        try:
            if os.path.exists('output/indigenous_nations.md'):
                with open('output/indigenous_nations.md', 'r') as f:
                    indigenous_content = f.read()
                    # Ensure proper Markdown formatting and line breaks
                    # Replace any problematic characters and ensure consistent formatting
                    indigenous_content = indigenous_content.replace('\n\n', '\n')
                    # Make sure bullet points are properly formatted
                    indigenous_content = indigenous_content.replace('*   ', '* ')
                    response_data["indigenous_nations"] = indigenous_content
        except Exception as e:
            print(f"Error reading indigenous_nations.md: {e}")
        
        # Read next steps if file exists
        try:
            if os.path.exists('output/next_steps.md'):
                with open('output/next_steps.md', 'r') as f:
                    next_steps_content = f.read()
                    # Parse the next steps into structured format
                    next_steps = []
                    
                    # Split the content by numbered items (1., 2., 3.)
                    import re
                    # Find all numbered items with their explanations
                    step_pattern = r'(\d+\.)\s+(.*?)(?=\d+\.\s+|\Z)'
                    matches = re.findall(step_pattern, next_steps_content, re.DOTALL)
                    
                    for _, match in matches:
                        # The first line is the step title, the rest is the explanation
                        lines = [line.strip() for line in match.strip().split('\n')]
                        if lines:
                            step = lines[0]
                            explanation = ' '.join(lines[1:]) if len(lines) > 1 else ""
                            next_steps.append({
                                "step": step,
                                "explanation": explanation
                            })
                    
                    # If regex didn't work, fall back to the original approach
                    if not next_steps:
                        current_step = None
                        explanation_lines = []
                        
                        for line in next_steps_content.split('\n'):
                            if line.strip():
                                if line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                                    # If we have a previous step, save it
                                    if current_step and explanation_lines:
                                        next_steps.append({
                                            "step": current_step,
                                            "explanation": ' '.join(explanation_lines)
                                        })
                                        explanation_lines = []
                                    
                                    # Extract the step text (after the number and period)
                                    parts = line.split('.', 1)
                                    if len(parts) > 1:
                                        current_step = parts[1].strip()
                                    else:
                                        current_step = line.strip()
                                elif current_step:
                                    # Add this line to the explanation
                                    explanation_lines.append(line.strip())
                        
                        # Add the last step if it exists
                        if current_step and explanation_lines:
                            next_steps.append({
                                "step": current_step,
                                "explanation": ' '.join(explanation_lines)
                            })
                    
                    response_data["next_steps"] = next_steps
        except Exception as e:
            print(f"Error reading next_steps.md: {e}")
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running EA scoping: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 