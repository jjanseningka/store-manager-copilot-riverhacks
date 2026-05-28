from __future__ import annotations

import json
import os
from typing import Any

import anthropic

from data.loader import DataStore
from llm.evaluators import critique_report, evaluate_chat_response, evaluate_report
from llm.memory import get_memory
from llm.prompts import REPORT_PROMPT, SYSTEM_PROMPT, TOOL_DEFINITIONS
from tools.actions import generate_daily_priorities
from tools.external_context import get_store_context
from tools.insights import generate_proactive_insights
from tools.margin import (
    get_hfb_margin_analysis,
    get_low_margin_alerts,
    get_margin_analysis,
    get_top_profitable_articles,
)
from tools.sales import (
    get_declining_articles,
    get_hfb_performance,
    get_sales_summary,
    get_sales_vs_forecast,
    get_top_articles,
)
from tools.stock import (
    get_availability_risks,
    get_oos_top_sellers,
    get_overstock_articles,
    get_stock_alerts,
)
from tools.whatif import whatif_availability_improvement, whatif_demand_surge, whatif_price_change

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 10


def _execute_tool(tool_name: str, tool_input: dict, store: DataStore, bu_sk: int) -> Any:
    """Dispatch a tool call to the appropriate analysis function."""
    dispatch: dict[str, Any] = {
        "get_sales_summary": lambda _: get_sales_summary(store, bu_sk),
        "get_sales_vs_forecast": lambda args: get_sales_vs_forecast(store, bu_sk, args["period"]),
        "get_top_articles": lambda args: get_top_articles(
            store, bu_sk, args["period"], args.get("n", 10), args.get("metric", "sales")
        ),
        "get_hfb_performance": lambda args: get_hfb_performance(store, bu_sk, args["period"]),
        "get_declining_articles": lambda args: get_declining_articles(
            store, bu_sk, args.get("n", 10)
        ),
        "get_stock_alerts": lambda _: get_stock_alerts(store, bu_sk),
        "get_availability_risks": lambda _: get_availability_risks(store, bu_sk),
        "get_oos_top_sellers": lambda _: get_oos_top_sellers(store, bu_sk),
        "get_overstock_articles": lambda _: get_overstock_articles(store, bu_sk),
        "get_margin_analysis": lambda args: get_margin_analysis(store, bu_sk, args["period"]),
        "get_top_profitable_articles": lambda args: get_top_profitable_articles(
            store, bu_sk, args["period"], args.get("n", 10)
        ),
        "get_low_margin_alerts": lambda args: get_low_margin_alerts(
            store, bu_sk, args.get("period", "30d")
        ),
        "get_hfb_margin_analysis": lambda args: get_hfb_margin_analysis(
            store, bu_sk, args["period"]
        ),
        "generate_daily_priorities": lambda _: generate_daily_priorities(store, bu_sk),
        "get_store_context": lambda _: get_store_context(store.today, bu_sk),
        "get_proactive_insights": lambda _: generate_proactive_insights(store, bu_sk),
        "whatif_price_change": lambda args: whatif_price_change(
            store, bu_sk, args["item_no"], args["price_change_pct"], args.get("period", "30d")
        ),
        "whatif_availability_improvement": lambda _: whatif_availability_improvement(store, bu_sk),
        "whatif_demand_surge": lambda args: whatif_demand_surge(
            store, bu_sk, args["demand_increase_pct"], args.get("period", "7d")
        ),
    }

    handler = dispatch.get(tool_name)
    if handler is None:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        return handler(tool_input)
    except Exception as e:
        return {"error": f"Tool {tool_name} failed: {e!s}"}


class RetailAgent:
    """Claude-powered retail expert with tool-calling capabilities."""

    def __init__(self, store: DataStore, bu_sk: int) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it in a .env file or export it in your shell."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.store = store
        self.bu_sk = bu_sk
        self.messages: list[dict] = []
        self.memory = get_memory()
        self.session_id: str = ""

        # Get store name for context
        bu_row = store.business_units[store.business_units["bu_sk"] == bu_sk]
        self.store_name = bu_row.iloc[0]["bu_name"] if len(bu_row) > 0 else f"Store {bu_sk}"

    def _get_system_prompt(self) -> str:
        base = (
            f"{SYSTEM_PROMPT}\n\n"
            f"## Current Context\n"
            f"- **Store**: {self.store_name}\n"
            f"- **Data as of**: {self.store.today.strftime('%A, %d %B %Y')}\n"
            f"- **Store ID (bu_sk)**: {self.bu_sk}\n"
        )
        # Inject memory context if available
        if self.session_id:
            mem_ctx = self.memory.get_context_for_llm(self.session_id, f"store_{self.bu_sk}")
            if mem_ctx:
                base += f"\n{mem_ctx}\n"
        return base

    def _run_conversation(self, messages: list[dict]) -> str:
        """Run a multi-turn conversation with tool-calling loop."""
        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self._get_system_prompt(),
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            # Check if we need to handle tool use
            if response.stop_reason == "tool_use":
                # Collect all tool results
                tool_results = []
                assistant_content = response.content

                for block in response.content:
                    if block.type == "tool_use":
                        result = _execute_tool(block.name, block.input, self.store, self.bu_sk)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, default=str),
                            }
                        )

                # Add assistant message and tool results to conversation
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})
            else:
                # Final response — extract text
                text_parts = [b.text for b in response.content if hasattr(b, "text")]
                return "\n".join(text_parts)

        return "I ran out of analysis rounds. Please try a more specific question."

    def chat(self, user_message: str) -> tuple[str, dict | None]:
        """Send a user message and get a response with lightweight evaluation.

        Flow:
        1. Generate response (tool-calling conversation)
        2. Evaluator checks quality → pass/fail
        3. If fail: retry once with the evaluator's hint

        Returns:
            (response_text, evaluation_result)
        """
        self.messages.append({"role": "user", "content": user_message})
        if self.session_id:
            self.memory.add_message(self.session_id, "user", user_message)

        # Build messages for API call (full history)
        result = self._run_conversation(list(self.messages))

        # --- Lightweight evaluation ---
        evaluation = None
        try:
            evaluation = evaluate_chat_response(user_message, result)
            if not evaluation.get("pass", True):
                # Retry once with the evaluator's feedback
                hint = evaluation.get("revision_hint", "")
                issues = ", ".join(evaluation.get("issues", []))
                retry_prompt = (
                    f"Your previous answer had quality issues: {issues}. "
                    f"Hint: {hint}. "
                    f"Please answer the original question again, addressing these issues. "
                    f"Original question: {user_message}"
                )
                retry_messages = list(self.messages)
                retry_messages.append({"role": "assistant", "content": result})
                retry_messages.append({"role": "user", "content": retry_prompt})
                result = self._run_conversation(retry_messages)
                # Re-evaluate
                try:
                    evaluation = evaluate_chat_response(user_message, result)
                except Exception:
                    pass
        except Exception:
            pass

        self.messages.append({"role": "assistant", "content": result})
        if self.session_id:
            self.memory.add_message(self.session_id, "assistant", result)
        return result, evaluation

    def generate_report(self) -> tuple[str, dict | None]:
        """Generate the daily commercial briefing with critic-refine-evaluate loop.

        Flow:
        1. Generate draft report (tool-calling conversation)
        2. Critic reviews the draft → structured feedback
        3. If critic says 'needs_revision': refine with feedback
        4. Evaluator scores the final version → pass/fail with rubric

        Returns:
            (report_text, evaluation_result)
        """
        # --- Step 1: Generate draft ---
        messages = [{"role": "user", "content": REPORT_PROMPT}]
        draft = self._run_conversation(messages)

        # --- Step 2: Critic reviews ---
        try:
            critique = critique_report(draft)
        except Exception:
            # If critic fails, return draft as-is
            return draft, None

        quality = critique.get("overall_quality", "good")

        # --- Step 3: Refine if needed ---
        if quality in ("needs_revision", "poor"):
            revision_instructions = critique.get("revision_instructions", "")
            issues_text = "\n".join(
                f"- [{i['severity']}] {i['section']}: {i['issue']} → {i['suggestion']}"
                for i in critique.get("issues", [])
            )
            refine_prompt = (
                f"Your draft was reviewed. Here is the feedback:\n\n"
                f"**Quality**: {quality}\n\n"
                f"**Issues**:\n{issues_text}\n\n"
                f"**Revision instructions**: {revision_instructions}\n\n"
                f"Please revise the report to address ALL issues above. "
                f"Keep all the data you already gathered — just improve the presentation, "
                f"fill gaps, and strengthen actionability. Output the complete revised report."
            )
            # Continue the conversation with the critique
            messages.append({"role": "assistant", "content": draft})
            messages.append({"role": "user", "content": refine_prompt})
            draft = self._run_conversation(messages)

        # --- Step 4: Final evaluation ---
        try:
            evaluation = evaluate_report(draft)
        except Exception:
            evaluation = None

        return draft, evaluation

    def reset_history(self) -> None:
        """Clear conversation history."""
        self.messages = []
