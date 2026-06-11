# Week 5: TechCorp Agent with Gemini Tool Use

AIPI-561 Operationalizing AI | Jaideep Aher

## What this is

This project builds a small agentic AI system for TechCorp. Gemini 2.5 Pro decides which tool to call, the app executes that tool against real TechCorp data, and Gemini then writes a grounded answer based on the tool result.

The agent can:

- look up employees from a SQLite database
- search internal policy documents
- answer expense approval limit questions
- track token usage and estimated query cost
- run locally in Python or through a deployed Streamlit app

## Repo structure

```text
.
+-- app_starter.py           # agent, tools, Gemini loop, metrics
+-- streamlit_app.py         # deployed chat UI
+-- run_agent_tests.py       # 10-query report generator
+-- REPORT.md                # test results and screenshot
+-- requirements.txt
+-- railway.json             # Railway deployment config
+-- data/
|   +-- techcorp.db
|   +-- documents.json
|   +-- policies.json
|   +-- access_control.json
+-- screenshots/
    +-- deployed_app.png
```

## How to run

```bash
cd week5
python3 -m pip install -r requirements.txt
export GOOGLE_API_KEY="your-key-here"

# quick CLI test
python3 app_starter.py

# generate the 10-query report
python3 run_agent_tests.py

# run the web app
python3 -m streamlit run streamlit_app.py
```

## Deployment

The app is deployed on Railway with `streamlit_app.py` as the entrypoint.

- Live app: `https://web-production-58c21.up.railway.app`

Railway expects the `GOOGLE_API_KEY` environment variable to be set in the service configuration.

## Notes

- The retrieval tool returns ranked snippets centered around matching terms so policy answers are better grounded.
- Token counts come from Gemini usage metadata when available, with a lightweight fallback estimate if metadata is absent.
- Week 5 keeps access control as role context only. The dataset still includes sensitive fields because Week 6 is where permissions get enforced.
