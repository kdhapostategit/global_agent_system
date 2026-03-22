import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

@CrewBase
class DailySocialsCrew:
    """Daily Socials Crew - High Volume Output"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def get_knowledge_sources(self):
        """Scans the /knowledge folder and passes ONLY the filenames."""
        sources = []
        knowledge_dir = "knowledge" 
        
        if os.path.exists(knowledge_dir):
            for file_name in os.listdir(knowledge_dir):
                if file_name.endswith('.txt'):
                    sources.append(TextFileKnowledgeSource(file_paths=[file_name]))
                elif file_name.endswith('.pdf'):
                    sources.append(PDFKnowledgeSource(file_paths=[file_name]))
        return sources

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
        return Agent(
            config=self.agents_config["chief_editor"],
            knowledge_sources=self.get_knowledge_sources()
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
            embedder={
                "provider": "google-generativeai",
                "config": {
                    "model": "gemini-embedding-001"
                }
            }
        )