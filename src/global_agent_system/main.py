#!/usr/bin/env python
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any, cast

import gspread
import requests
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from opentelemetry import baggage
from pydantic import BaseModel

from crewai.flow import Flow, listen, router, start

from global_agent_system.crews.daily_socials_crew.daily_socials_crew import DailySocialsCrew
from global_agent_system.crews.poem_crew.poem_crew import PoemCrew

# Load .env before any crew/knowledge code reads API keys or embedder config.
load_dotenv()

_GSHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _parse_chief_editor_rows(raw: str) -> list[list[str]]:
    """Parse Chief Editor output into A–E column values. Handles optional brackets."""
    rows: list[list[str]] = []
    # Split by ITEM followed by a number and colon/dash (Extremely Loose Version)
    items = re.split(r"ITEM\s*\d+\s*[:\-]", raw, flags=re.IGNORECASE)
    
    for chunk in items:
        if not chunk.strip(): 
            continue
        
        # 1. Topic: Take the first non-empty line
        topic_lines = [line.strip() for line in chunk.strip().split('\n') if line.strip()]
        topic = topic_lines[0] if topic_lines else "Unknown Topic"
        
        # 2. URL: Find the first https link
        url_match = re.search(r"https?://\S+", chunk)
        url = url_match.group(0) if url_match else "No URL Found"
        
        # 3. Renditions: Split by the three keywords
        parts = re.split(r"Short\s+Rendition|Medium\s+Rendition|Long\s+Rendition", chunk, flags=re.IGNORECASE)
        
        if len(parts) >= 4:
            # Cleanup: remove leftover characters like [ ] : *
            short = parts[1].strip().strip('[]:* ').strip()
            medium = parts[2].strip().strip('[]:* ').strip()
            long = parts[3].strip().strip('[]:* ').strip()
            rows.append([topic, url, short, medium, long])
            
    return rows


def send_to_google_sheets(chief_editor_raw: str) -> None:
    """Delivers data to the first available row based on Column A, keeping checkboxes intact."""
    cred_env = os.environ.get("DAILY_SOCIALS_GOOGLE_CREDENTIALS")
    sheet_id = os.environ.get("DAILY_SOCIALS_GOOGLE_SHEET_ID")
    if not cred_env or not sheet_id:
        print(
            "Skipping Google Sheets: set DAILY_SOCIALS_GOOGLE_CREDENTIALS and "
            "DAILY_SOCIALS_GOOGLE_SHEET_ID"
        )
        return

    cred_path = os.path.abspath(os.path.expanduser(cred_env))
    if not os.path.isfile(cred_path):
        print(f"Skipping Google Sheets: credentials file not found: {cred_path}")
        return

    parsed = _parse_chief_editor_rows(chief_editor_raw or "")
    if not parsed:
        print(
            "Google Sheets: no rows parsed from Chief Editor output; nothing appended."
        )
        return

    try:
        creds = Credentials.from_service_account_file(cred_path, scopes=_GSHEETS_SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id.strip())
        worksheet = spreadsheet.worksheet("Daily Socials Review")

        # --- SMART FILLER LOGIC ---
        # 1. Get all values in Column A to see where the topics end
        col_a_values = worksheet.col_values(1)
        
        # 2. Find the next available row starting from Row 2
        start_row = 2
        for i, val in enumerate(col_a_values):
            if i == 0: continue # Skip header
            if not val or val.strip() == "":
                start_row = i + 1
                break
        else:
            start_row = len(col_a_values) + 1
            
        # 3. Define the range from Column A to E
        end_row = start_row + len(parsed) - 1
        target_range = f"A{start_row}:E{end_row}"
        
        # 4. Update the range instead of appending, so it ignores Column F checkboxes
        worksheet.update(range_name=target_range, values=parsed, value_input_option="USER_ENTERED")
        print(f"🚀 Google Sheets: Successfully parked {len(parsed)} items starting at Row {start_row}.")

    except Exception as e:
        print(f"Google Sheets delivery failed: {e}")


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
        # Default: Daily Socials Crew. Poem Crew only when the topic explicitly mentions "poem".
        if "poem" in self.state.topic.lower():
            return "poem_path"
        return "social_path"

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
        send_to_google_sheets(result.raw)


# --- NEW SCHEDULER LOGIC ---

def is_office_hours() -> bool:
    """Checks if current time is M-F, 8 AM to 8 PM - BYPASSED FOR TESTING"""
    # now = datetime.now()
    # is_weekday = now.weekday() <= 4  # 0=Mon, 4=Fri
    # is_time_window = 8 <= now.hour < 20
    # return is_weekday and is_time_window
    return True


def sync_google_docs():
    """Fetches the latest version of public Google Docs as plain text."""
    print("🔄 Syncing live knowledge base from Google Docs...")

    # Using the /export?format=txt endpoint to download clean text
    docs_to_sync = {
        "kevins_philosophy_source.txt": (
            "https://docs.google.com/document/d/"
            "13i1J1jOfdZFGOcd4eNYNU0ki8Q4f1h-AUR8jZnjMAR4/export?format=txt"
        ),
    }

    knowledge_dir = os.path.join(
        os.path.dirname(__file__), "../../knowledge/daily_socials_knowledge"
    )
    os.makedirs(knowledge_dir, exist_ok=True)

    for filename, url in docs_to_sync.items():
        try:
            response = requests.get(url)
            response.raise_for_status()

            filepath = os.path.join(knowledge_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ Successfully updated: {filename}")
        except Exception as e:
            print(
                f"❌ Failed to update {filename}. Using cached local version. Error: {e}"
            )


def kickoff():
    """Switch between single-run (Testing) and continuous-loop (Production)"""
    sync_google_docs()
    print("--- Global Agent System Started ---")
    
    # --- OPTION A: POEM CREW TEST (Deactivated) ---
    # print(f"[{datetime.now()}] GM: Running Poem Crew test cycle...")
    # agent_flow = AgentFlow()
    # agent_flow.kickoff(inputs={"topic": "Write a short haiku about a robot"})
    # print(f"[{datetime.now()}] GM: Poem test complete.")

    # --- OPTION B: SOCIAL CREW SINGLE RUN (Activated for Sheets Test) ---
    print(f"[{datetime.now()}] GM: Running single Social Crew cycle...")
    agent_flow = AgentFlow()
    agent_flow.kickoff(inputs={"topic": "Create daily social options across 3 beats"})
    print(f"[{datetime.now()}] GM: Social test complete.")

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