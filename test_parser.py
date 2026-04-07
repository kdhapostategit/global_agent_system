import re
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

# THE MOCK DATA (Copy-pasted from your terminal output)
MOCK_OUTPUT = """
ITEM 1: Sam Altman States Superintelligence Is So Close, America Needs New Social Contract
Source URL: 
https://www.reddit.com/r/singularity/comments/1se5dcs/altman_social_contract/

Short Rendition 
Altman’s call for a "new social contract" isn't abstract; it's a stark admission that AGI's arrival demands wealth redistribution.

Medium Rendition
The conversation around AI just got a material upgrade. Sam Altman isn't just hypothesizing; he's laying down blueprints for a transition.

Long Rendition
Let me pause and speak plainly: when the CEO of a leading AI firm articulates the need for a "new social contract" akin to the New Deal...

ITEM 2: AI Models Are Independently Conducting Scientific Research
Source URL: 
https://www.reddit.com/r/accelerate/comments/1se32gb/ai_research/

Short Rendition 
AI isn't just executing tasks. It's discovering.

Medium Rendition
The news that AI models are now independently conducting scientific research is a profound friction point.

Long Rendition
We have, for centuries, anchored our sense of self in discovery. Now, the machine learns, synthesizes, and creates beyond our guidance.
"""

def extremely_loose_parser(raw):
    rows = []
    # Split by ITEM followed by a number and colon/dash
    items = re.split(r"ITEM\s*\d+\s*[:\-]", raw, flags=re.IGNORECASE)
    
    for chunk in items:
        if not chunk.strip(): continue
        
        # 1. Topic: Just take the first line
        topic_lines = [line.strip() for line in chunk.strip().split('\n') if line.strip()]
        topic = topic_lines[0] if topic_lines else "Unknown Topic"
        
        # 2. URL: Find the first https link
        url_match = re.search(r"https?://\S+", chunk)
        url = url_match.group(0) if url_match else "No URL Found"
        
        # 3. Renditions: Split by keywords
        parts = re.split(r"Short\s+Rendition|Medium\s+Rendition|Long\s+Rendition", chunk, flags=re.IGNORECASE)
        
        if len(parts) >= 4:
            short = parts[1].strip().strip('[]:* ').strip()
            medium = parts[2].strip().strip('[]:* ').strip()
            long = parts[3].strip().strip('[]:* ').strip()
            rows.append([topic, url, short, medium, long])
            print(f"✅ Parsed: {topic[:40]}...")
    
    return rows

def test_delivery():
    rows = extremely_loose_parser(MOCK_OUTPUT)
    if not rows:
        print("❌ Parser failed to find any rows.")
        return

    cred_env = os.getenv("DAILY_SOCIALS_GOOGLE_CREDENTIALS")
    sheet_id = os.getenv("DAILY_SOCIALS_GOOGLE_SHEET_ID")
    
    try:
        creds = Credentials.from_service_account_file(
            cred_env, 
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets", 
                "https://www.googleapis.com/auth/drive"
            ]
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet("Daily Socials Review")

        # --- THE "TOP-FIRST" LOGIC ---
        # Get every value in Column A. This returns a list of strings.
        col_a = ws.col_values(1)
        
        # We want to find the first empty row starting from Row 2 (index 1)
        start_row = 2
        for i, val in enumerate(col_a):
            if i == 0: continue # Skip the "Topic" header
            if not val or val.strip() == "":
                start_row = i + 1
                break
        else:
            # If no empty cells were found in the middle, start after the last entry
            start_row = len(col_a) + 1

        # Calculate the range to update
        end_row = start_row + len(rows) - 1
        target_range = f"A{start_row}:E{end_row}"
        
        # Update the sheet starting from the top
        ws.update(range_name=target_range, values=rows, value_input_option="USER_ENTERED")
        
        print(f"🚀 SUCCESS! Data parked at Row {start_row} through {end_row}.")
        print("Go check the TOP of your Google Sheet!")
        
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_delivery()