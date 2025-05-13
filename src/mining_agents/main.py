#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime
import json

from mining_agents.crew import MiningAgents

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Ensure the output directory exists
os.makedirs('output', exist_ok=True)

def get_user_input():
    """Get project parameters from user via CLI interaction"""
    print("\n=== Mining Project Environmental Assessment Scoping ===\n")
    print("Please provide the following information for your mining project:\n")
    
    project_name = input("1. Project name: ")
    location_region = input("2. General location (region in BC, e.g., Skeena, Kootenay): ")
    cobalt_type = input("3. Type of cobalt mineralization (e.g., 'Sediment-Hosted Stratiform'): ")
    
    while True:
        scale = input("4. Estimated operational scale (Small, Medium, Large): ").capitalize()
        if scale in ["Small", "Medium", "Large"]:
            break
        print("Please enter 'Small', 'Medium', or 'Large'")
    
    inputs = {
        'project_name': project_name,
        'location_region': location_region,
        'cobalt_type': cobalt_type,
        'scale': scale
    }
    
    # Save the inputs to a file for reference
    with open('output/user_inputs.json', 'w') as f:
        json.dump(inputs, f, indent=2)
    
    return inputs

def load_mock_data():
    """Load mock data from a predefined file"""
    try:
        with open('mock_input.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default mock data if file not found
        return {
            'project_name': 'Northern Cobalt Initiative',
            'location_region': 'Skeena',
            'cobalt_type': 'Sediment-Hosted Stratiform',
            'scale': 'Large'
        }

def run():
    """
    Run the mining agents crew for EA scoping.
    """
    # Ask if user wants to use mock data
    use_mock = input("\nUse mock data for demonstration? (y/n): ").lower().strip() == 'y'
    
    # Get inputs either from user or mock data
    if use_mock:
        inputs = load_mock_data()
        print("\n=== Starting Mining Agents EA Scoping Demo with Mock Data ===\n")
    else:
        inputs = get_user_input()
        print("\n=== Starting Mining Agents EA Scoping Demo ===\n")
    
    print("Project parameters:")
    for key, value in inputs.items():
        print(f"  - {key}: {value}")
    print("\nProcessing with agent crew...\n")
    
    try:
        result = MiningAgents().crew().kickoff(inputs=inputs)
        print("\n=== EA Scoping Results ===\n")
        print(result.raw)
        print("\nResults have been saved to the output directory.")
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = load_mock_data()
    try:
        MiningAgents().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        MiningAgents().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = load_mock_data()
    
    try:
        MiningAgents().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    run()
