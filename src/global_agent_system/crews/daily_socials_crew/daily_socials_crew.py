from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool

from global_agent_system.tools.custom_tool import RSSFeedTool

# 1. Create a tool that strictly searches the Google News tab for the last 24 hours (tbs=qdr:d)
news_search_tool = SerperDevTool(
    search_url="https://google.serper.dev/news",
    search_params={"tbs": "qdr:d"} 
)

# 2. Create a tool that pulls directly from a reliable Christian/Religion news feed
religion_rss_tool = RSSFeedTool(feed_url='https://religionnews.com/feed/')

@CrewBase
class DailySocialsCrew:
    """Daily Socials Crew - High Volume Output"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # --- AGENTS ---
    @agent
    def ai_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["ai_researcher"],
            tools=[
                RSSFeedTool(),
                news_search_tool,
                ScrapeWebsiteTool(),
                FileReadTool(),
            ],
        )

    @agent
    def culture_politics_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["culture_politics_researcher"],
            tools=[
                RSSFeedTool(),
                news_search_tool,
                ScrapeWebsiteTool(),
                FileReadTool(),
            ],
        )

    @agent
    def religion_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["religion_researcher"],
            tools=[
                religion_rss_tool,   # It checks the direct feed first
                news_search_tool,    # It searches Google News (last 24 hours only)
                ScrapeWebsiteTool(), # It clicks and reads the articles it finds
                FileReadTool(),      # It reads your rubric
            ],
        )

    @agent
    def data_cleaner(self) -> Agent:
        return Agent(
            config=self.agents_config["data_cleaner"],
            tools=[FileReadTool()],
        )

    @agent
    def ai_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["ai_writer"],
            tools=[FileReadTool()],
        )

    @agent
    def religion_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["religion_writer"],
            tools=[FileReadTool()],
        )

    @agent
    def culture_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["culture_writer"],
            tools=[FileReadTool()],
        )

    @agent
    def chief_editor(self) -> Agent:
        return Agent(
            config=self.agents_config["chief_editor"],
            tools=[FileReadTool()],
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
    def clean_ai_data(self) -> Task:
        return Task(config=self.tasks_config["clean_ai_data"])

    @task
    def clean_culture_data(self) -> Task:
        return Task(config=self.tasks_config["clean_culture_data"])

    @task
    def clean_religion_data(self) -> Task:
        return Task(config=self.tasks_config["clean_religion_data"])

    @task
    def write_ai_social_options(self) -> Task:
        return Task(config=self.tasks_config["write_ai_social_options"])

    @task
    def write_culture_social_options(self) -> Task:
        return Task(config=self.tasks_config["write_culture_social_options"])

    @task
    def write_religion_social_options(self) -> Task:
        return Task(config=self.tasks_config["write_religion_social_options"])

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
            output_log_file='logs/crew_run.txt'
        )