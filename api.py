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
                    response_data["regulatory_check"] = f.read()
        except Exception as e:
            print(f"Error reading regulatory_check.md: {e}")
        
        # Read project description outline if file exists
        try:
            if os.path.exists('output/pd_outline.md'):
                with open('output/pd_outline.md', 'r') as f:
                    pd_content = f.read()
                    # Parse into sections
                    sections = {}
                    current_section = None
                    content_lines = []
                    
                    for line in pd_content.split('\n'):
                        if line.startswith('**'):  # Section header
                            # Save previous section if it exists
                            if current_section and content_lines:
                                sections[current_section] = '\n'.join(content_lines)
                                content_lines = []
                            # Extract new section name
                            current_section = line.strip('*').strip()
                        elif line.strip() and current_section:
                            content_lines.append(line)
                    
                    # Save final section
                    if current_section and content_lines:
                        sections[current_section] = '\n'.join(content_lines)
                    
                    response_data["pd_outline"] = sections
        except Exception as e:
            print(f"Error reading pd_outline.md: {e}")
            
        # Read indigenous nations info if file exists
        try:
            if os.path.exists('output/indigenous_nations.md'):
                with open('output/indigenous_nations.md', 'r') as f:
                    response_data["indigenous_nations"] = f.read()
        except Exception as e:
            print(f"Error reading indigenous_nations.md: {e}")
        
        # Read next steps if file exists
        try:
            if os.path.exists('output/next_steps.md'):
                with open('output/next_steps.md', 'r') as f:
                    next_steps_content = f.read()
                    # Parse the next steps into structured format
                    next_steps = []
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
                                current_step = line.split('.', 1)[1].strip()
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