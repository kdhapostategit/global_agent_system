#!/usr/bin/env python
import json
import sys
import time
from datetime import datetime
from typing import Any, cast

from dotenv import load_dotenv

from opentelemetry import baggage
from pydantic import BaseModel

from crewai.flow import Flow, listen, router, start

from global_agent_system.crews.daily_socials_crew.daily_socials_crew import DailySocialsCrew
from global_agent_system.crews.poem_crew.poem_crew import PoemCrew

# Load .env before any crew/knowledge code reads API keys or embedder config.
load_dotenv()


class AgentState(BaseModel):
    topic: str = ""
    content_output: str = ""
    status: str = "pending"


class AgentFlow(Flow[AgentState]):
    @start()
    def accept_user_input(self) -> None:
        inputs = cast(dict[str, Any], baggage.get_baggage("flow_inputs") or {})
        topic = inputs.get("topic", self.state.topic)
        self.state.topic = topic if isinstance(topic, str) else str(topic)

    @router(accept_user_input)
    def route_by_topic(self, _result: Any) -> str:
        if "social" in self.state.topic.lower():
            return "social_path"
        return "poem_path"

    @listen("poem_path")
    def run_poem_crew(self, _result: Any) -> None:
        result = (
            PoemCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topic})
        )
        self.state.content_output = result.raw

    @listen("social_path")
    def run_daily_socials_crew(self, _result: Any) -> None:
        result = (
            DailySocialsCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topic})
        )
        self.state.content_output = result.raw


# --- NEW SCHEDULER LOGIC ---

def is_office_hours() -> bool:
    """Checks if current time is M-F, 8 AM to 8 PM - BYPASSED FOR TESTING"""
    # now = datetime.now()
    # is_weekday = now.weekday() <= 4  # 0=Mon, 4=Fri
    # is_time_window = 8 <= now.hour < 20
    # return is_weekday and is_time_window
    return True


def kickoff():
    """Switch between single-run (Testing) and continuous-loop (Production)"""
    print("--- Global Agent System Started ---")
    
    # --- OPTION A: POEM CREW TEST (Currently Active) ---
    print(f"[{datetime.now()}] GM: Running Poem Crew test cycle...")
    agent_flow = AgentFlow()
    # The router sends anything WITHOUT the word "social" to the poem path
    agent_flow.kickoff(inputs={"topic": "Write a short haiku about a robot"})
    print(f"[{datetime.now()}] GM: Poem test complete.")

    # --- OPTION B: SOCIAL CREW SINGLE RUN (Commented out for now) ---
    # print(f"[{datetime.now()}] GM: Running single Social Crew cycle...")
    # agent_flow = AgentFlow()
    # agent_flow.kickoff(inputs={"topic": "Create daily social options across 3 beats"})
    # print(f"[{datetime.now()}] GM: Social test complete.")

    # --- OPTION C: SCHEDULER LOOP (Commented out for Production) ---
    # while True:
    #     if is_office_hours():
    #         print(f"[{datetime.now()}] GM: Starting a new 4-hour cycle...")
    #         agent_flow = AgentFlow()
    #         agent_flow.kickoff(inputs={"topic": "Create daily social options across 3 beats"})
    #         print(f"[{datetime.now()}] GM: Cycle complete. Sleeping for 4 hours.")
    #         time.sleep(14400)
    #     else:
    #         print(f"[{datetime.now()}] GM: Outside office hours. Checking again in 30 mins.")
    #         time.sleep(1800)


def plot():
    agent_flow = AgentFlow()
    agent_flow.plot()


def run_with_trigger():
    """
    Run the flow with trigger payload.
    """
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    agent_flow = AgentFlow()

    try:
        topic = trigger_payload.get(
            "topic",
            "Create a social post about AI Agents",
        )
        result = agent_flow.kickoff(inputs={"topic": topic})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}") from e


if __name__ == "__main__":
    kickoff()