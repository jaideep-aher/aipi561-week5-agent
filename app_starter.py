import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import google.genai as genai
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
INPUT_COST_PER_1M = 0.075
OUTPUT_COST_PER_1M = 0.3

class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, **kwargs) -> str:
        raise NotImplementedError

class EmployeeLookupTool(Tool):
    def __init__(self, db_path: str):
        super().__init__("employee_lookup", "Find employee information by name or ID")
        self.db_path = db_path

    def execute(self, employee_name: str = None, employee_id: str = None) -> str:
        try:
            if not employee_name and not employee_id:
                return "Provide employee_name or employee_id."

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if employee_id:
                    cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
                else:
                    cursor.execute(
                        "SELECT * FROM employees WHERE name LIKE ? LIMIT 10",
                        (f"%{employee_name}%",),
                    )
                rows = [dict(row) for row in cursor.fetchall()]

            if not rows:
                return "Employee not found"

            return json.dumps(rows, indent=2, default=str)
        except Exception as e:
            logger.error(f"Employee lookup error: {e}")
            return f"Error: {str(e)}"


class PolicySearchTool(Tool):
    def __init__(self):
        super().__init__("policy_search", "Search policy documents by keyword or topic")
        documents_path = DATA_DIR / "documents.json"
        with documents_path.open("r", encoding="utf-8") as f:
            self.documents = json.load(f)

    def execute(self, query: str, limit: int = 5) -> str:
        try:
            if not query:
                return "Provide a query to search policies."

            normalized_query = query.lower().strip()
            stopwords = {
                "the",
                "what",
                "which",
                "are",
                "for",
                "and",
                "policy",
                "policies",
                "documented",
                "list",
                "show",
                "tell",
                "about",
            }
            terms = [
                term
                for term in re.findall(r"[a-z0-9_]+", normalized_query)
                if len(term) > 2 and term not in stopwords
            ]
            broad_policy_request = any(
                phrase in normalized_query
                for phrase in [
                    "policy",
                    "policies",
                    "handbook",
                    "guidelines",
                    "documents",
                ]
            )

            if broad_policy_request and not terms:
                matches = self._policy_catalog(max(1, int(limit)))
                return json.dumps(matches, indent=2)

            scored_documents = []
            for doc in self.documents:
                title = doc.get("title", "")
                content = doc.get("content", "")
                category = doc.get("category", "")
                haystack = f"{title} {category} {content}".lower()
                title_lower = title.lower()
                score = sum(haystack.count(term) for term in terms)
                score += sum(title_lower.count(term) * 3 for term in terms)
                if normalized_query in haystack:
                    score += 5
                if any(word in title_lower for word in ["policy", "handbook"]):
                    score += 2
                if "sales territory" in title_lower:
                    score -= 3
                if score > 0:
                    scored_documents.append((score, doc))

            scored_documents.sort(key=lambda item: item[0], reverse=True)
            matches = scored_documents[: max(1, int(limit))]

            if not matches:
                if broad_policy_request:
                    matches = self._policy_catalog(max(1, int(limit)))
                    return json.dumps(matches, indent=2)
                return f"No policy documents found for: {query}"

            results = []
            for score, doc in matches:
                content = " ".join(doc.get("content", "").split())
                results.append(
                    {
                        "id": doc.get("id"),
                        "title": doc.get("title"),
                        "category": doc.get("category"),
                        "last_updated": doc.get("last_updated"),
                        "score": score,
                        "snippet": self._make_snippet(content, terms),
                    }
                )

            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Policy search error: {e}")
            return f"Error: {str(e)}"

    def _policy_catalog(self, limit: int) -> list:
        catalog = []
        for doc in self.documents:
            title = doc.get("title", "")
            title_lower = title.lower()
            if "sales territory" in title_lower:
                continue
            if not any(word in title_lower for word in ["policy", "handbook", "guidelines"]):
                continue
            content = " ".join(doc.get("content", "").split())
            catalog.append(
                {
                    "id": doc.get("id"),
                    "title": title,
                    "category": doc.get("category"),
                    "last_updated": doc.get("last_updated"),
                    "score": 1,
                    "snippet": content[:500],
                }
            )
        return catalog[:limit]

    def _make_snippet(self, content: str, terms: list) -> str:
        lower_content = content.lower()
        match_positions = [
            lower_content.find(term) for term in terms if lower_content.find(term) >= 0
        ]
        if not match_positions:
            return content[:500]

        start = max(0, min(match_positions) - 180)
        end = min(len(content), start + 500)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(content) else ""
        return f"{prefix}{content[start:end]}{suffix}"

class ExpenseQueryTool(Tool):
    def __init__(self):
        super().__init__("expense_query", "Query expense approval limits by role")
        policies_path = DATA_DIR / "policies.json"
        with policies_path.open("r", encoding="utf-8") as f:
            self.policies = json.load(f)

    def execute(self, role: str) -> str:
        try:
            if not role:
                return "Provide a role. Valid roles: ic1_ic2, ic3, manager, director, vp"

            normalized_role = role.lower().strip().replace(" ", "_").replace("-", "_")
            aliases = {
                "engineer": "ic3",
                "senior_engineer": "ic3",
                "individual_contributor": "ic3",
                "ic1": "ic1_ic2",
                "ic2": "ic1_ic2",
            }
            normalized_role = aliases.get(normalized_role, normalized_role)
            approval_limits = self.policies.get("expense", {}).get("approval_limits", {})
            amount = approval_limits.get(normalized_role)

            if amount is None:
                return f"Role not found: {role}"

            return f"Approval limit for {normalized_role}: ${amount:,.0f}"
        except Exception as e:
            logger.error(f"Expense query error: {e}")
            return f"Error: {str(e)}"

class Agent:
    def __init__(self, db_path: str, api_key: str = None):
        self.db_path = db_path
        self.api_key = api_key or GOOGLE_API_KEY

        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. Get free key at: "
                "https://aistudio.google.com/app/apikey"
            )

        self.client = genai.Client(api_key=self.api_key)
        self.tools = {
            "employee_lookup": EmployeeLookupTool(db_path),
            "policy_search": PolicySearchTool(),
            "expense_query": ExpenseQueryTool(),
        }
        self.token_count = 0
        self.total_cost = 0.0
        self.queries_run = 0

    def _build_system_prompt(self, user_role: str) -> str:
        tool_list = "\n".join(
            f"- {tool.name}: {tool.description}" for tool in self.tools.values()
        )
        return f"""
You are a TechCorp business assistant. Decide which single tool best answers
the user's question, then return a JSON object and no other text.

User role: {user_role}

Available tools:
{tool_list}

Tool argument schemas:
- employee_lookup: {{"employee_name": "partial name"}} or {{"employee_id": "exact id"}}
- policy_search: {{"query": "policy keywords", "limit": 3}}
- expense_query: {{"role": "ic1_ic2|ic3|manager|director|vp"}}

Return exactly one of these shapes:
{{"tool": "employee_lookup", "args": {{"employee_name": "Brian Yang"}}}}
{{"tool": "policy_search", "args": {{"query": "travel policy", "limit": 3}}}}
{{"tool": "expense_query", "args": {{"role": "manager"}}}}
{{"tool": "none", "args": {{}}}}
""".strip()

    def query(self, user_query: str, user_role: str = "engineer") -> Dict[str, Any]:
        logger.info(f"Processing query: {user_query}")

        input_tokens = 0
        output_tokens = 0
        tool_call: Dict[str, Any] = {"tool": "none", "args": {}}
        tool_result = ""

        try:
            system_prompt = self._build_system_prompt(user_role)
            planning_prompt = f"{system_prompt}\n\nUser question: {user_query}"
            planning_response = self.client.models.generate_content(
                model=MODEL_ID,
                contents=planning_prompt,
            )
            plan_text = self._response_text(planning_response)
            plan_input, plan_output = self._usage_tokens(planning_response, planning_prompt, plan_text)
            input_tokens += plan_input
            output_tokens += plan_output

            tool_call = self._parse_tool_call(plan_text) or self._fallback_tool_call(user_query)
            tool_name = tool_call.get("tool", "none")
            tool_args = tool_call.get("args", {})

            if tool_name in self.tools:
                tool_result = self.tools[tool_name].execute(**tool_args)
            else:
                tool_result = "No tool was needed or no matching tool was available."

            synthesis_prompt = f"""
You are a TechCorp assistant. Answer the user's question clearly and concisely
using only the tool result below. If the result does not answer the question,
say what is missing.

User role: {user_role}
User question: {user_query}
Tool used: {tool_name}
Tool arguments: {json.dumps(tool_args)}
Tool result:
{tool_result}
""".strip()
            final_response = self.client.models.generate_content(
                model=MODEL_ID,
                contents=synthesis_prompt,
            )
            answer = self._response_text(final_response)
            final_input, final_output = self._usage_tokens(final_response, synthesis_prompt, answer)
            input_tokens += final_input
            output_tokens += final_output
        except Exception as e:
            logger.exception("Agent query failed")
            fallback_call = self._fallback_tool_call(user_query)
            fallback_tool = fallback_call.get("tool", "none")
            if fallback_tool in self.tools:
                tool_result = self.tools[fallback_tool].execute(**fallback_call.get("args", {}))
                answer = (
                    "Gemini was unavailable, so I used the local tool fallback.\n\n"
                    f"{tool_result}"
                )
                tool_call = fallback_call
            else:
                answer = f"Error while processing query: {str(e)}"

        tokens_used = input_tokens + output_tokens
        cost = self._estimate_query_cost(input_tokens, output_tokens)
        self.token_count += tokens_used
        self.total_cost += cost
        self.queries_run += 1

        return {
            "answer": answer,
            "tokens_used": tokens_used,
            "cost": cost,
            "role": user_role,
            "tool_call": tool_call,
            "tool_result": tool_result,
        }

    def _response_text(self, response: Any) -> str:
        text = getattr(response, "text", None)
        if text:
            return text.strip()
        return str(response).strip()

    def _usage_tokens(self, response: Any, prompt: str, output: str) -> Tuple[int, int]:
        metadata = getattr(response, "usage_metadata", None)
        if metadata:
            input_tokens = getattr(metadata, "prompt_token_count", None)
            output_tokens = getattr(metadata, "candidates_token_count", None)
            if input_tokens is not None and output_tokens is not None:
                return int(input_tokens), int(output_tokens)

        estimated_input = max(1, len(prompt.split()) * 4 // 3)
        estimated_output = max(1, len(output.split()) * 4 // 3)
        return estimated_input, estimated_output

    def _parse_tool_call(self, response_text: str) -> Optional[Dict[str, Any]]:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return None

        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        tool_name = parsed.get("tool", "none")
        args = parsed.get("args", {})
        if not isinstance(args, dict):
            args = {}
        return {"tool": tool_name, "args": args}

    def _fallback_tool_call(self, user_query: str) -> Dict[str, Any]:
        query = user_query.lower()
        role_pattern = r"\b(ic1_ic2|ic1|ic2|ic3|manager|director|vp|engineer|senior engineer)\b"
        role_match = re.search(role_pattern, query)

        if any(term in query for term in ["approval limit", "expense limit", "spending limit"]):
            return {
                "tool": "expense_query",
                "args": {"role": role_match.group(1).replace(" ", "_") if role_match else "manager"},
            }

        if any(term in query for term in ["employee", "who is", "look up", "lookup"]):
            id_match = re.search(r"\b(?:id|employee id)\s*#?:?\s*(\d+)\b", query)
            if id_match:
                return {"tool": "employee_lookup", "args": {"employee_id": id_match.group(1)}}
            name_match = re.search(r"(?:employee|who is|look up|lookup)\s+([a-z][a-z\s'-]+)", user_query, re.I)
            employee_name = name_match.group(1).strip(" ?.") if name_match else user_query
            return {"tool": "employee_lookup", "args": {"employee_name": employee_name}}

        return {"tool": "policy_search", "args": {"query": user_query, "limit": 3}}

    def _estimate_query_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
        return input_cost + output_cost

    def get_metrics(self) -> Dict[str, Any]:
        avg_cost = self.total_cost / self.queries_run if self.queries_run else 0.0
        return {
            "total_queries": self.queries_run,
            "total_tokens": self.token_count,
            "total_cost": self.total_cost,
            "avg_cost_per_query": avg_cost,
        }

if __name__ == "__main__":
    import sys

    try:
        agent = Agent(str(DATA_DIR / "techcorp.db"))
        print("Agent initialized successfully")

        print("\nTesting query: 'What is the travel policy?'")
        result = agent.query("What is the travel policy?")
        print(f"Answer: {result['answer']}")
        print(f"Tokens: {result['tokens_used']}")
        print(f"Cost: ${result['cost']:.6f}")

        metrics = agent.get_metrics()
        print(f"\nMetrics: {metrics}")

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Error during test")
        sys.exit(1)
