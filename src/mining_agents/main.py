#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from mining_agents.crew import MiningAgents

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Ensure the output directory exists
os.makedirs('output', exist_ok=True)

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the mining agents crew for EA scoping.
    """
    # For demo purposes, we can either use hardcoded values or we could
    # implement interactive input through a simple command-line interface
    # Here we use hardcoded values for consistency and simplicity
    inputs = {
        'project_name': 'Northern Cobalt Initiative',
        'location_region': 'Skeena',
        'cobalt_type': 'Sediment-Hosted Stratiform',
        'scale': 'Large'
    }
    
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
    inputs = {
        'project_name': 'Northern Cobalt Initiative',
        'location_region': 'Skeena',
        'cobalt_type': 'Sediment-Hosted Stratiform',
        'scale': 'Large'
    }
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
    inputs = {
        'project_name': 'Northern Cobalt Initiative',
        'location_region': 'Skeena',
        'cobalt_type': 'Sediment-Hosted Stratiform',
        'scale': 'Large'
    }
    
    try:
        MiningAgents().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    run()
