import os
from pathlib import Path

import streamlit as st

from app_starter import Agent


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "techcorp.db"

ROLE_OPTIONS = {
    "engineer": "Engineer",
    "manager": "Manager",
    "hr": "HR",
    "finance": "Finance",
    "executive": "Executive",
}

EXAMPLE_QUESTIONS = [
    "What is the travel policy?",
    "Look up employee Brian Yang",
    "What is the expense approval limit for a manager?",
    "Which policies are documented in the handbook?",
]

WELCOME_MESSAGE = (
    "Hi, I am the TechCorp assistant. Ask me about employees, company "
    "policies, or expense approval limits and I will use the right tool to "
    "find the answer."
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(1200px 600px at 15% -10%, #1d2440 0%, #0d1020 55%, #080a14 100%);
        }
        .tc-hero {
            border-radius: 18px;
            padding: 28px 32px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(56, 189, 248, 0.10));
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 18px 45px rgba(8, 10, 20, 0.45);
            margin-bottom: 22px;
        }
        .tc-hero h1 {
            margin: 0;
            font-size: 2.1rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #f8fafc;
        }
        .tc-hero p {
            margin: 8px 0 0 0;
            color: #aeb9d4;
            font-size: 1.02rem;
            max-width: 640px;
        }
        .tc-badge {
            display: inline-block;
            margin-bottom: 14px;
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #c7d2fe;
            background: rgba(99, 102, 241, 0.22);
            border: 1px solid rgba(129, 140, 248, 0.35);
        }
        .tc-metric {
            border-radius: 14px;
            padding: 16px 18px;
            background: rgba(20, 26, 46, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.16);
            height: 100%;
        }
        .tc-metric .label {
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #8a96b4;
        }
        .tc-metric .value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-top: 4px;
        }
        .tc-section-title {
            font-size: 0.78rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #8a96b4;
            margin: 6px 0 10px 0;
        }
        section[data-testid="stSidebar"] {
            background: rgba(11, 14, 26, 0.92);
            border-right: 1px solid rgba(148, 163, 184, 0.12);
        }
        .stChatMessage {
            border-radius: 14px;
        }
        div[data-testid="stChatInput"] textarea {
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="tc-hero">
            <span class="tc-badge">TechCorp Policy Pilot</span>
            <h1>TechCorp Agent</h1>
            <p>An AI assistant that routes every question to the right internal
            tool, looking up employees, searching company policy, and checking
            expense approval limits in real time.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(metrics: dict) -> None:
    cols = st.columns(4)
    cards = [
        ("Queries", f"{metrics['total_queries']}"),
        ("Tokens", f"{metrics['total_tokens']:,}"),
        ("Total cost", f"${metrics['total_cost']:.4f}"),
        ("Avg per query", f"${metrics['avg_cost_per_query']:.4f}"),
    ]
    for col, (label, value) in zip(cols, cards):
        col.markdown(
            f"""
            <div class="tc-metric">
                <div class="label">{label}</div>
                <div class="value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


@st.cache_resource
def load_agent() -> Agent:
    return Agent(str(DB_PATH), api_key=os.getenv("GOOGLE_API_KEY"))


def run_query(agent: Agent, prompt: str, user_role: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Reasoning with Gemini and TechCorp tools"):
            result = agent.query(prompt, user_role=user_role)
        st.write(result["answer"])
        tool_call = result.get("tool_call") or {}
        tool_name = tool_call.get("tool", "none")
        st.caption(
            f"Tool: {tool_name} | Tokens: {result['tokens_used']:,} | "
            f"Cost: ${result['cost']:.6f}"
        )
        with st.expander("Run details"):
            st.json(
                {
                    "tool_call": tool_call,
                    "tokens_used": result["tokens_used"],
                    "cost": result["cost"],
                    "metrics": agent.get_metrics(),
                }
            )

    st.session_state.messages.append(
        {"role": "assistant", "content": result["answer"]}
    )


def main() -> None:
    st.set_page_config(
        page_title="TechCorp Agent",
        page_icon="TC",
        layout="wide",
    )
    inject_styles()

    agent_error = None
    try:
        agent = load_agent()
    except Exception as exc:
        agent = None
        agent_error = str(exc)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

    with st.sidebar:
        st.markdown('<div class="tc-section-title">Session</div>', unsafe_allow_html=True)
        user_role = st.selectbox(
            "Acting as role",
            options=list(ROLE_OPTIONS.keys()),
            format_func=lambda value: ROLE_OPTIONS[value],
            index=0,
        )
        st.caption(
            "Week 5 accepts role context. Week 6 will enforce permissions per "
            "role."
        )

        st.markdown('<div class="tc-section-title">Try an example</div>', unsafe_allow_html=True)
        for index, question in enumerate(EXAMPLE_QUESTIONS):
            if st.button(question, key=f"example_{index}", use_container_width=True):
                st.session_state.pending_prompt = question

        st.markdown('<div class="tc-section-title">Controls</div>', unsafe_allow_html=True)
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": WELCOME_MESSAGE}
            ]
            st.session_state.pending_prompt = None
            st.rerun()

    render_hero()

    if agent_error:
        st.error(f"Agent could not start: {agent_error}")
        st.info(
            "Set the GOOGLE_API_KEY environment variable with a free key from "
            "https://aistudio.google.com/app/apikey and reload the page."
        )
        st.stop()

    render_metrics(agent.get_metrics())
    st.divider()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    typed_prompt = st.chat_input("Ask a TechCorp question")
    prompt = typed_prompt or st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    if prompt:
        run_query(agent, prompt, user_role)
        st.rerun()


if __name__ == "__main__":
    main()
