"""Run the 10-query Week 5 report test set."""

import json
from pathlib import Path

from app_starter import Agent


BASE_DIR = Path(__file__).resolve().parent
REPORT_PATH = BASE_DIR / "REPORT.md"

TEST_QUERIES = [
    ("What is the travel policy?", "engineer"),
    ("What is the PTO policy for managers?", "manager"),
    ("What is the parental leave policy?", "engineer"),
    ("What is the expense approval limit for a manager?", "manager"),
    ("What is the spending limit for a VP?", "executive"),
    ("Look up employee Brian Yang", "hr"),
    ("Who is employee ID 2?", "finance"),
    ("What benefits policies are documented?", "engineer"),
    ("What is the code of conduct?", "engineer"),
    ("What is the approval limit for ic3?", "engineer"),
]


def main() -> None:
    agent = Agent(str(BASE_DIR / "data" / "techcorp.db"))
    rows = []

    for index, (question, role) in enumerate(TEST_QUERIES, start=1):
        result = agent.query(question, user_role=role)
        rows.append(
            {
                "number": index,
                "question": question,
                "role": role,
                "tool": result.get("tool_call", {}).get("tool"),
                "tokens": result["tokens_used"],
                "cost": result["cost"],
                "answer": result["answer"],
            }
        )
        print(f"{index}. {question}")
        print(result["answer"])
        print()

    metrics = agent.get_metrics()
    report = [
        "# Week 5 Agent Report",
        "",
        "## Summary",
        "",
        "The TechCorp agent uses Gemini to choose one of three tools, executes the selected tool, and asks Gemini to synthesize a grounded answer from the tool result.",
        "",
        "## Test Results",
        "",
        "| # | Role | Question | Tool | Tokens | Cost |",
        "|---|---|---|---|---:|---:|",
    ]

    for row in rows:
        report.append(
            f"| {row['number']} | {row['role']} | {row['question']} | {row['tool']} | {row['tokens']} | ${row['cost']:.6f} |"
        )

    report.extend(
        [
            "",
            "## Metrics",
            "",
            f"```json\n{json.dumps(metrics, indent=2)}\n```",
            "",
            "## Detailed Answers",
            "",
        ]
    )

    for row in rows:
        report.extend(
            [
                f"### {row['number']}. {row['question']}",
                "",
                f"- Role: `{row['role']}`",
                f"- Tool: `{row['tool']}`",
                f"- Tokens: `{row['tokens']}`",
                f"- Cost: `${row['cost']:.6f}`",
                "",
                row["answer"],
                "",
            ]
        )

    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
