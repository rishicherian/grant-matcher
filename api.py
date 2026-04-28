import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.agent import run_project_stage, run_profile_stage, run_ranking_stage
from core.guardrails import validate_user_prompt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stages = [
    {
        "name": "project_info",
        "questions": [
            {
                "name": "project_area",
                "question": "What is the main area of your project?"
            },
            {
                "name": "project_description",
                "question": "Please describe your project in a few sentences."
            },
            {
                "name": "target_population",
                "question": "Who is the target population for your project?"
            },
            {
                "name": "research_focus",
                "question": "What is your research focus or specific project focus? You can say N/A if none."
            },
        ],
    },
    {
        "name": "profile_info",
        "questions": [
            {
                "name": "applicant_type",
                "question": "What type of applicant are you? For example: student, nonprofit, individual, business."
            },
            {
                "name": "location",
                "question": "What is your location? For example: city, state."
            },
            {
                "name": "budget_needed",
                "question": "How much funding do you need?"
            },
        ],
    },
    {
        "name": "ranking_decision",
        "questions": [
            {
                "name": "ranking_choice",
                "question": "Would you like me to rank the eligible grants with explanations? Yes or No."
            }
        ],
    },
]


def parse_budget(value: str):
    matches = re.findall(r"[\d,]+(?:\.\d+)?", value)
    if not matches:
        return None
    try:
        return float(matches[0].replace(",", ""))
    except ValueError:
        return None


def serialize_project_grants(project_matches):
    return [
        {
            "id": grant.get("id", "unknown"),
            "grant_title": grant.get("metadata", {}).get("grant_title", "Unknown Title"),
            "summary_text": grant.get("summary_text", ""),
            "metadata": grant.get("metadata", {}),
        }
        for grant in project_matches
    ]


def serialize_profile_grants(grants):
    return [
        {
            "id": grant.get("id", "unknown"),
            "grant_title": grant.get("metadata", {}).get("grant_title", "Unknown Title"),
            "summary_text": grant.get("summary_text", ""),
            "metadata": grant.get("metadata", {}),
            "eligible": grant.get("eligible", False),
            "eligible_reasons": grant.get("eligible_reasons", []),
            "ineligible_reasons": grant.get("ineligible_reasons", []),
        }
        for grant in grants
    ]


@app.post("/query")
async def query_agent(data: dict):
    message = data.get("message", "").strip()
    project_info = data.get("project_info", {})
    user_profile = data.get("user_profile", {})
    project_matches = data.get("project_matches", [])
    eligible_grants = data.get("eligible_grants", [])
    current_stage = data.get("current_stage", 0)
    current_question = data.get("current_question", 0)

    if message.lower() in ["restart", "reset"]:
        return {
            "type": "question",
            "question": stages[0]["questions"][0]["question"],
            "project_info": {},
            "user_profile": {},
            "project_matches": [],
            "eligible_grants": [],
            "current_stage": 0,
            "current_question": 0,
        }

    stage = stages[current_stage]

    bypass_words = {"n/a", "optional", "yes", "no", "y", "n", "sure", "ok", "yes please"}
    
    if message and message.lower() not in bypass_words:
        guardrail_result = validate_user_prompt(message)
        
        if not guardrail_result.get("is_valid", True):
            reason = guardrail_result.get("reason", "Please keep your responses focused on grant matching.")
            return {
                "type": "question",
                "question": f"⚠️ **Off-Topic Detected:** {reason}\n\nLet's try again: {stage['questions'][current_question]['question']}",
                "project_info": project_info,
                "user_profile": user_profile,
                "project_matches": project_matches,
                "eligible_grants": eligible_grants,
                "current_stage": current_stage,
                "current_question": current_question,
            }

    if stage["name"] == "project_info":
        if not message:
            return {
                "type": "question",
                "question": stage["questions"][0]["question"],
                "project_info": project_info,
                "user_profile": user_profile,
                "project_matches": [],
                "eligible_grants": [],
                "current_stage": 0,
                "current_question": 0,
            }

        field_name = stage["questions"][current_question]["name"]
        project_info[field_name] = "" if message.lower() == "optional" else message
        current_question += 1

        if current_question < len(stage["questions"]):
            return {
                "type": "question",
                "question": stage["questions"][current_question]["question"],
                "project_info": project_info,
                "user_profile": user_profile,
                "project_matches": [],
                "eligible_grants": [],
                "current_stage": current_stage,
                "current_question": current_question,
            }

        try:
            results = run_project_stage(project_info)
            project_matches = results.get("project_matches", [])
            serialized_project_matches = serialize_project_grants(project_matches)

            grant_lines = []
            for i, grant in enumerate(serialized_project_matches, start=1):
                title = grant["grant_title"]
                summary = grant.get("summary_text", "")
                short_summary = summary[:180] + "..." if len(summary) > 180 else summary
                grant_lines.append(f"{i}. {title}\n ")

            message_text = (
                f"I found {len(project_matches)} grants related to your project:\n\n"
                + "\n\n".join(grant_lines)
            )

            return {
                "type": "stage_complete",
                "stage": "project_info_complete",
                "message": message_text,
                "project_info": project_info,
                "user_profile": user_profile,
                "project_matches": project_matches,
                "eligible_grants": [],
                "project_match_results": serialized_project_matches,
                "next_question": stages[1]["questions"][0]["question"],
                "current_stage": 1,
                "current_question": 0,
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error during project matching: {str(e)}"
            }

    if stage["name"] == "profile_info":
        if not message:
            return {
                "type": "question",
                "question": stage["questions"][current_question]["question"],
                "project_info": project_info,
                "user_profile": user_profile,
                "project_matches": project_matches,
                "eligible_grants": eligible_grants,
                "current_stage": current_stage,
                "current_question": current_question,
            }

        field_name = stage["questions"][current_question]["name"]
        if field_name == "budget_needed":
            user_profile[field_name] = parse_budget(message)
        else:
            user_profile[field_name] = message

        current_question += 1

        if current_question < len(stage["questions"]):
            return {
                "type": "question",
                "question": stage["questions"][current_question]["question"],
                "project_info": project_info,
                "user_profile": user_profile,
                "project_matches": project_matches,
                "eligible_grants": eligible_grants,
                "current_stage": current_stage,
                "current_question": current_question,
            }

        try:
            if not project_matches:
                project_stage_results = run_project_stage(project_info)
                project_matches = project_stage_results.get("project_matches", [])

            results = run_profile_stage(
                project_info=project_info,
                user_profile=user_profile,
                project_matches=project_matches,
            )

            eligible_grants = results.get("eligible_grants", [])
            ineligible_grants = results.get("ineligible_grants", [])
            all_evaluated = results.get("all_evaluated_grants", [])

            serialized_eligible = serialize_profile_grants(eligible_grants)
            serialized_ineligible = serialize_profile_grants(ineligible_grants)
            serialized_all = serialize_profile_grants(all_evaluated)

            if serialized_eligible:
                grant_lines = []
                for i, grant in enumerate(serialized_eligible, start=1):
                    title = grant["grant_title"]
                    summary = grant.get("summary_text", "")
                    short_summary = summary[:180] + "..." if len(summary) > 180 else summary
                    grant_lines.append(f"{i}. {title}\n")

                message_text = (
                    f"I found {len(eligible_grants)} eligible grants:\n\n"
                    + "\n\n".join(grant_lines)
                )

                return {
                    "type": "stage_complete",
                    "stage": "profile_info_complete",
                    "message": message_text,
                    "project_info": project_info,
                    "user_profile": user_profile,
                    "project_matches": project_matches,
                    "eligible_grants": eligible_grants,
                    "profile_match_results": {
                        "eligible_grants": serialized_eligible,
                        "ineligible_grants": serialized_ineligible,
                        "all_evaluated_grants": serialized_all,
                    },
                    "next_question": stages[2]["questions"][0]["question"],
                    "current_stage": 2,
                    "current_question": 0,
                }
            else:
                message_text = (
                    f"I found 0 eligible grants and {len(ineligible_grants)} grants that do not appear eligible."
                )

                return {
                    "type": "final_results",
                    "message": message_text + "\n\nWould you like to try again with different criteria? Type 'restart' to begin a new search.",
                    "project_info": project_info,
                    "user_profile": user_profile,
                    "project_matches": project_matches,
                    "eligible_grants": [],
                }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error during profile matching: {str(e)}"
            }

    if stage["name"] == "ranking_decision":
        answer = message.lower()

        if answer in {"yes", "y", "sure", "ok", "yes please"}:
            try:
                if not project_matches:
                    project_stage_results = run_project_stage(project_info)
                    project_matches = project_stage_results.get("project_matches", [])

                if not eligible_grants:
                    profile_stage_results = run_profile_stage(
                        project_info=project_info,
                        user_profile=user_profile,
                        project_matches=project_matches,
                    )
                    eligible_grants = profile_stage_results.get("eligible_grants", [])

                print("RANKING STAGE project_matches count:", len(project_matches))
                print("RANKING STAGE eligible_grants count:", len(eligible_grants))

                if not eligible_grants:
                    return {
                        "type": "final_results",
                        "message": "I could not find any eligible grants to rank.",
                        "project_info": project_info,
                        "user_profile": user_profile,
                        "project_matches": project_matches,
                        "eligible_grants": [],
                        "ranked_results": [],
                    }

                results = run_ranking_stage(
                    project_info=project_info,
                    user_profile=user_profile,
                    eligible_grants=eligible_grants,
                )

                if not results.get("success"):
                    return {
                        "type": "error",
                        "message": results.get("message", "Ranking failed.")
                    }

                return {
                    "type": "final_results",
                    "message": "Here are your ranked eligible grants.",
                    "project_info": project_info,
                    "user_profile": user_profile,
                    "project_matches": project_matches,
                    "eligible_grants": eligible_grants,
                    "ranked_results": results.get("ranked_results", []),
                }

            except Exception as e:
                print("RANKING ERROR:", repr(e))
                return {
                    "type": "error",
                    "message": f"Error during ranking: {str(e)}"
                }

        return {
            "type": "final_results",
            "message": "Okay, here are your eligible grants without ranking.",
            "project_info": project_info,
            "user_profile": user_profile,
            "project_matches": project_matches,
            "eligible_grants": serialize_profile_grants(eligible_grants),
        }

    return {
        "type": "error",
        "message": "Invalid chatbot state."
    }


@app.get("/")
async def root():
    return {"message": "Grant Matcher API"}