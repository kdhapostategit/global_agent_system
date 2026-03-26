from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class DailySocialsCrew:
    """Daily Socials Crew - High Volume Output"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # --- AGENTS ---
    @agent
    def ai_researcher(self) -> Agent:
        return Agent(config=self.agents_config["ai_researcher"])

    @agent
    def culture_politics_researcher(self) -> Agent:
        return Agent(config=self.agents_config["culture_politics_researcher"])

    @agent
    def religion_researcher(self) -> Agent:
        return Agent(config=self.agents_config["religion_researcher"])

    @agent
    def data_cleaner(self) -> Agent:
        return Agent(config=self.agents_config["data_cleaner"])

    @agent
    def ai_writer(self) -> Agent:
        return Agent(config=self.agents_config["ai_writer"])

    @agent
    def religion_writer(self) -> Agent:
        return Agent(config=self.agents_config["religion_writer"])

    @agent
    def culture_writer(self) -> Agent:
        return Agent(config=self.agents_config["culture_writer"])

    @agent
    def chief_editor(self) -> Agent:
        return Agent(config=self.agents_config["chief_editor"])

    # --- TASKS ---
    @task
    def research_ai_trends(self) -> Task:
        return Task(config=self.tasks_config["research_ai_trends"])

    @task
    def research_culture_politics(self) -> Task:
        return Task(config=self.tasks_config["research_culture_politics"])

    @task
    def research_religion_nationalism(self) -> Task:
        return Task(config=self.tasks_config["research_religion_nationalism"])

    @task
    def clean_and_structure_data(self) -> Task:
        return Task(config=self.tasks_config["clean_and_structure_data"])

    @task
    def write_ai_social_options(self) -> Task:
        return Task(config=self.tasks_config["write_ai_social_options"])

    @task
    def write_religion_social_options(self) -> Task:
        return Task(config=self.tasks_config["write_religion_social_options"])

    @task
    def write_culture_social_options(self) -> Task:
        return Task(config=self.tasks_config["write_culture_social_options"])

    @task
    def edit_and_select_final_options(self) -> Task:
        return Task(config=self.tasks_config["edit_and_select_final_options"])

    # --- CREW ---
    @crew
    def crew(self) -> Crew:
        """Creates the Daily Socials Pipeline"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )