from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class MiningAgents():
    """Mining Agents crew for EA scoping and initial assessment"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    @agent
    def project_intake_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['project_intake_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def regulatory_check_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['regulatory_check_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def pd_outline_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['pd_outline_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def indigenous_nation_id_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['indigenous_nation_id_agent'], # type: ignore[index]
            verbose=True
        )

    @task
    def project_intake_task(self) -> Task:
        return Task(
            config=self.tasks_config['project_intake_task'], # type: ignore[index]
            output_file='output/project_parameters.md'
        )

    @task
    def regulatory_check_task(self) -> Task:
        return Task(
            config=self.tasks_config['regulatory_check_task'], # type: ignore[index]
            context=[self.project_intake_task()],
            output_file='output/regulatory_check.md'
        )

    @task
    def pd_outline_task(self) -> Task:
        return Task(
            config=self.tasks_config['pd_outline_task'], # type: ignore[index]
            context=[self.project_intake_task()],
            output_file='output/pd_outline.md'
        )

    @task
    def indigenous_nation_id_task(self) -> Task:
        return Task(
            config=self.tasks_config['indigenous_nation_id_task'], # type: ignore[index]
            context=[self.project_intake_task()],
            output_file='output/indigenous_nations.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Mining Agents crew for EA scoping"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
