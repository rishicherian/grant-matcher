# Grant Matcher Agent

## Project layout

```text
grant-matcher/
├── core/
│   ├── agent.py
│   ├── profile_builder.py
│   ├── eligibility.py
│   ├── tools.py
│   ├── scraper.py
│   ├── data_parser.py
│   └── build_db.py
├── data/
│   ├── raw_markdown/
│   ├── processed_json/
│   └── chroma_db/
├── tests/
│   └── test_eligibility.py
├── requirements.txt
└── README.md
```

## Quick start

1. Create and activate virtual eviroment

```bash
python3 -m venv venv
source venv/bin/activate
```


2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your Mistral API key as an environment variable:

```bash
export MISTRAL_API_KEY=""
export MISTRAL_BASE_URL="https://api.mistral.ai/v1"
export MISTRAL_MODEL="mistral-small-latest"
```

4. Build the grant database:
```bash
python3 -m core.scraper
python3 -m core.data_parser
python3 -m core.build_db
```

5. run the application

Start backend (FastApi), runs on port 8001:
```bash
python3 -m uvicorn api:app --reload --port 8001
```

Start frontend (React), runs on http://localhost:3000:
```bash
cd frontend
npm install
npm start
```

## Notes
core/profile_builder.py builds a structured user profile from raw user input using rule-based extraction and optional LLM extraction.
core/tools.py retrieves relevant grant opportunities from the Chroma vector database.
core/eligibility.py classifies each retrieved grant as eligible, ineligible, or uncertain.
core/agent.py orchestrates the full workflow: profile extraction, retrieval, eligibility checking, ranking, and final output.
The agent expects grant data to be processed into data/processed_json/ and embedded into data/chroma_db/ before retrieval will work.
If the Mistral environment variables are not set, the system still runs, but profile extraction and ambiguous-case LLM review fall back to rule-based logic only.
