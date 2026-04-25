from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.agent import run_agent
import re

app = FastAPI()

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fields = [
    {"name": "organization_name", "question": "What's your name or organization name?"},
    {"name": "location", "question": "What's your location (city, state)?"},
    {"name": "applicant_type", "question": "What type of applicant are you (e.g., student, nonprofit, individual, business)?"},
    {"name": "project_area", "question": "What is the main area of your project (e.g., arts, education, health, research)?"},
    {"name": "target_population", "question": "Who is the target population for your project (e.g., youth, seniors, low-income communities)?"},
    {"name": "budget_needed", "question": "How much funding do you need (e.g., 5000)?"},
    {"name": "research_focus", "question": "What is your research focus (if applicable)?"}
]

@app.post("/query")
async def query_agent(data: dict):
    message = data.get("message", "").strip()
    profile = data.get("profile", {})
    current_step = data.get("current_step", 0)

    if message.lower() == "restart":
        return {
            "type": "question",
            "question": fields[0]["question"],
            "profile": {},
            "current_step": 0,
            "message": "Conversation restarted."
        }

    if message:
        field_name = fields[current_step]["name"]
        if field_name == "budget_needed":
            matches = re.findall(r"[\d,]+(?:\.\d+)?", message)
            if matches:
                try:
                    profile[field_name] = float(matches[0].replace(",", ""))
                except ValueError:
                    profile[field_name] = None
            else:
                profile[field_name] = None
        else:
            profile[field_name] = message
        current_step += 1

    if current_step < len(fields):
        return {
            "type": "question",
            "question": fields[current_step]["question"],
            "profile": profile,
            "current_step": current_step
        }
    else:
        # All fields filled, run agent
        profile["project_description"] = "Conversational input"
        try:
            results = run_agent(profile=profile)
            return {
                "type": "result",
                "result": results
            }
        except Exception as e:
            return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Grant Matcher API"}