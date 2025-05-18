from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
import uvicorn
from typing import Optional, List
import tempfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Import your mining agents
#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mining_agents.crew import MiningAgents

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
    logger.info("Root endpoint accessed")
    return {"status": "Mining Agents API is running"}

# Add a health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

@app.post("/run-ea-scoping", response_model=EAResponse)
async def run_ea_scoping(input_data: ProjectInput):
    """Run the EA scoping process with the mining agents"""
    logger.info(f"Starting EA scoping for project: {input_data.project_name}")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = 'output'
            # Prepare inputs for CrewAI
            inputs = {
                'project_name': input_data.project_name,
                'location_region': input_data.location_region,
                'cobalt_type': input_data.cobalt_type,
                'scale': input_data.scale
            }
            logger.debug(f"Input parameters: {inputs}")

            regulatory_md_path = os.path.join(temp_dir, 'regulatory_check.md')
            pd_md_path = os.path.join(temp_dir, 'pd_outline.md')
            indigenous_md_path = os.path.join(temp_dir, 'indigenous_nations.md')
            next_steps_md_path = os.path.join(temp_dir, 'next_steps.md')
            
            # Run the Crew
            logger.info("Initializing Mining Agents crew")
            result = MiningAgents(output_base_dir=temp_dir).crew().kickoff(inputs=inputs)
            logger.info("Mining Agents crew execution completed")
            print(result)
            
            # Read output files for response
            response_data = {
                "project_parameters": inputs
            }

            # Read regulatory check results if file exists
            if os.path.exists(regulatory_md_path):
                logger.debug(f"Reading regulatory check from {regulatory_md_path}")
                with open(regulatory_md_path, 'r') as f:
                    regulatory_content = f.read()
                    # Ensure proper Markdown formatting
                    regulatory_content = regulatory_content.replace('\n\n', '\n')
                    # Make sure bullet points are properly formatted
                    regulatory_content = regulatory_content.replace('*   ', '* ')
                    response_data["regulatory_check"] = regulatory_content
            else:
                logger.warning("Regulatory check file does not exist, for path %s", str(regulatory_md_path))
            
            # Read project description outline if file exists
            if os.path.exists(pd_md_path):
                logger.debug(f"Reading project description from {pd_md_path}")
                with open(pd_md_path, 'r') as f:
                    pd_content = f.read()
                    # Parse into sections
                    sections = {}
                    current_section = None
                    content_lines = []
                    
                    # Use a regex approach to extract sections more reliably
                    import re
                    # Find all section headers and their content
                    section_pattern = r'\*\*(.*?)\*\*(.*?)(?=\*\*.*?\*\*|\Z)'
                    matches = re.findall(section_pattern, pd_content, re.DOTALL)
                    
                    if matches:
                        logger.debug(f"Found {len(matches)} sections in project description")
                        for section_name, content in matches:
                            # Clean up the section name and content
                            clean_section = section_name.strip()
                            clean_content = content.strip()
                            sections[clean_section] = clean_content
                    else:
                        # Fall back to the original approach if regex fails
                        logger.warning("Regex pattern failed to match project description sections, falling back to alternative parsing")
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
            else:
                logger.warning("Project description outline file does not exist, for path %s", str(pd_md_path))
                
            # Read indigenous nations info if file exists
            if os.path.exists(indigenous_md_path):
                logger.debug(f"Reading indigenous nations info from {indigenous_md_path}")
                with open(indigenous_md_path, 'r') as f:
                    indigenous_content = f.read()
                    # Ensure proper Markdown formatting and line breaks
                    # Replace any problematic characters and ensure consistent formatting
                    indigenous_content = indigenous_content.replace('\n\n', '\n')
                    # Make sure bullet points are properly formatted
                    indigenous_content = indigenous_content.replace('*   ', '* ')
                    response_data["indigenous_nations"] = indigenous_content
            else:
                logger.warning("Indigenous nations info file does not exist, for path %s", str(indigenous_md_path))
        
            # Read next steps if file exists
            if os.path.exists(next_steps_md_path):
                logger.debug(f"Reading next steps from {next_steps_md_path}")
                with open(next_steps_md_path, 'r') as f:
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
            else:
                logger.warning("Next steps file does not exist for path %s", str(next_steps_md_path))
        
        logger.info(f"EA scoping for project {input_data.project_name} completed successfully")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in EA scoping process: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error running EA scoping: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Mining Agents API server")
    uvicorn.run("mining_agents.api:app", host="0.0.0.0", port=8000, reload=True) 