import os
import logging
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any

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

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

def prepend_slash(path: str) -> str:
    # Crew chops off the leading slash, so we need to add two slashes to ensure the file is created relative to the root
    # https://github.com/crewAIInc/crewAI/blob/bef59715987ba52c94710b0c0c77745fb4ce5185/src/crewai/task.py#L308
    # NOTE: UGLY WORKAROUND, REMOVE ASAP
    if path.startswith('/'):
        return '/' + path
    return path

@CrewBase
class MiningAgents():
    """Mining Agents crew for EA scoping and initial assessment"""

    agents: List[BaseAgent]
    tasks: List[Task]
    output_base_dir: str = 'output'

    def __init__(self, output_base_dir: str):
        logger.info(f"Initializing MiningAgents with output_base_dir: {output_base_dir}")
        self.output_base_dir = output_base_dir


    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    @agent
    def project_intake_agent(self) -> Agent:
        logger.info("Creating project_intake_agent")
        return Agent(
            config=self.agents_config['project_intake_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def regulatory_check_agent(self) -> Agent:
        logger.info("Creating regulatory_check_agent")
        return Agent(
            config=self.agents_config['regulatory_check_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def pd_outline_agent(self) -> Agent:
        logger.info("Creating pd_outline_agent")
        return Agent(
            config=self.agents_config['pd_outline_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def indigenous_nation_id_agent(self) -> Agent:
        logger.info("Creating indigenous_nation_id_agent")
        return Agent(
            config=self.agents_config['indigenous_nation_id_agent'], # type: ignore[index]
            verbose=True
        )
        
    @agent
    def next_steps_agent(self) -> Agent:
        logger.info("Creating next_steps_agent")
        return Agent(
            config=self.agents_config['next_steps_agent'], # type: ignore[index]
            verbose=True
        )

    @task
    def project_intake_task(self) -> Task:
        logger.info("Creating project_intake_task")
        output_file = str(os.path.join(self.output_base_dir, 'project_parameters.md'))
        output_file = prepend_slash(output_file)
        logger.info(f"project_intake_task output file: {output_file}")
        task_instance = Task(
            config=self.tasks_config['project_intake_task'], # type: ignore[index]
            output_file=output_file,
            callback=lambda output: logger.info("Project intake task completed\n%s", output)
        )
        return task_instance

    @task
    def regulatory_check_task(self) -> Task:
        logger.info("Creating regulatory_check_task")
        output_file = str(os.path.join(self.output_base_dir, 'regulatory_check.md'))
        output_file = prepend_slash(output_file)
        logger.info(f"regulatory_check_task output file: {output_file}")
        task_instance = Task(
            config=self.tasks_config['regulatory_check_task'], # type: ignore[index]
            context=[self.project_intake_task()],
            output_file=output_file,
            callback=lambda output: logger.info("Regulatory check task completed\n%s", output)
        )
        return task_instance

    @task
    def pd_outline_task(self) -> Task:
        logger.info("Creating pd_outline_task")
        output_file = str(os.path.join(self.output_base_dir, 'pd_outline.md'))
        output_file = prepend_slash(output_file)
        logger.info(f"pd_outline_task output file: {output_file}")
        task_instance = Task(
            config=self.tasks_config['pd_outline_task'], # type: ignore[index]
            context=[self.project_intake_task()],
            output_file=output_file,
            callback=lambda output: logger.info("Project description outline task completed\n%s", output)
        )
        return task_instance

    @task
    def indigenous_nation_id_task(self) -> Task:
        logger.info("Creating indigenous_nation_id_task")
        output_file = str(os.path.join(self.output_base_dir, 'indigenous_nations.md'))
        output_file = prepend_slash(output_file)
        logger.info(f"indigenous_nation_id_task output file: {output_file}")
        task_instance = Task(
            config=self.tasks_config['indigenous_nation_id_task'], # type: ignore[index]
            context=[self.project_intake_task()],
            output_file=output_file,
            callback=lambda output: logger.info("Indigenous nation identification task completed\n%s", output)
        )
        return task_instance
        
    @task
    def next_steps_task(self) -> Task:
        logger.info("Creating next_steps_task")
        output_file = str(os.path.join(self.output_base_dir, 'next_steps.md'))
        output_file = prepend_slash(output_file)
        logger.info(f"next_steps_task output file: {output_file}")
        task_instance = Task(
            config=self.tasks_config['next_steps_task'], # type: ignore[index]
            context=[
                self.project_intake_task(),
                self.regulatory_check_task(),
                self.pd_outline_task(),
                self.indigenous_nation_id_task()
            ],
            output_file=output_file,
            callback=lambda output: logger.info("Next steps task completed\n%s", output)
        )
        return task_instance

    @crew
    def crew(self) -> Crew:
        """Creates the Mining Agents crew for EA scoping"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge
        logger.info("Creating Mining Agents crew")
        try:
            logger.info(f"Configuring crew with {len(self.agents)} agents and {len(self.tasks)} tasks")
            crew_instance = Crew(
                agents=self.agents, # Automatically created by the @agent decorator
                tasks=self.tasks, # Automatically created by the @task decorator
                process=Process.sequential,
                verbose=True,
            )
            logger.info("Mining Agents crew created successfully")
            return crew_instance
        except Exception as e:
            logger.error(f"Error creating Mining Agents crew: {str(e)}", exc_info=True)
            raise
