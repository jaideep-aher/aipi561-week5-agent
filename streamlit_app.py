"""Streamlit UI for the Week 5 TechCorp agent."""

import os
from pathlib import Path

import streamlit as st

from app_starter import Agent


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "techcorp.db"


st.set_page_config(page_title="TechCorp Agent", page_icon="TC", layout="wide")
st.title("TechCorp Agent")

with st.sidebar:
    st.subheader("Session")
    user_role = st.selectbox(
        "Role",
        ["engineer", "manager", "hr", "finance", "executive"],
        index=0,
    )
    st.caption("Week 5 accepts role context; Week 6 will enforce permissions.")


@st.cache_resource
def load_agent() -> Agent:
    return Agent(str(DB_PATH), api_key=os.getenv("GOOGLE_API_KEY"))


try:
    agent = load_agent()
except Exception as exc:
    st.error(f"Agent could not start: {exc}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ask me about employees, policies, or expense approval limits.",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask a TechCorp question")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Reasoning with Gemini and TechCorp tools..."):
            result = agent.query(prompt, user_role=user_role)
        st.write(result["answer"])
        with st.expander("Run details"):
            st.json(
                {
                    "tool_call": result.get("tool_call"),
                    "tokens_used": result["tokens_used"],
                    "cost": result["cost"],
                    "metrics": agent.get_metrics(),
                }
            )

    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
