from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool, SerperDevTool, FileReadTool

@CrewBase
class DailySocialsCrew:
    """Daily Socials Crew - High Volume Output"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    search_tool = SerperDevTool()
    scrape_tool = ScrapeWebsiteTool()
    ai_rubric_tool = FileReadTool(file_path='knowledge/ai_researcher_rubric.txt')
    culture_rubric_tool = FileReadTool(file_path='knowledge/culture_researcher_rubric.txt')
    religion_rubric_tool = FileReadTool(file_path='knowledge/religion_researcher_rubric.txt')
    cleaner_rubric_tool = FileReadTool(file_path='knowledge/data_cleaner_rubric.txt')
    writer_rubric_tool = FileReadTool(file_path='knowledge/social_writer_rubric.txt')
    editor_rubric_tool = FileReadTool(file_path='knowledge/chief_editor_rubric.txt')

    # --- AGENTS ---
    @agent
    def ai_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["ai_researcher"],
            tools=[self.search_tool, self.scrape_tool, self.ai_rubric_tool],
        )

    @agent
    def culture_politics_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["culture_politics_researcher"],
            tools=[self.search_tool, self.scrape_tool, self.culture_rubric_tool],
        )

    @agent
    def religion_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["religion_researcher"],
            tools=[self.search_tool, self.scrape_tool, self.religion_rubric_tool],
        )

    @agent
    def data_cleaner(self) -> Agent:
        return Agent(
            config=self.agents_config["data_cleaner"],
            tools=[self.cleaner_rubric_tool],
        )

    @agent
    def ai_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["ai_writer"],
            tools=[self.writer_rubric_tool],
        )

    @agent
    def religion_writer(self) -> Agent:
        return Agent(config=self.agents_config["religion_writer"])

    @agent
    def culture_writer(self) -> Agent:
        return Agent(config=self.agents_config["culture_writer"])

    @agent
    def chief_editor(self) -> Agent:
        return Agent(
            config=self.agents_config["chief_editor"],
            tools=[self.editor_rubric_tool],
        )

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