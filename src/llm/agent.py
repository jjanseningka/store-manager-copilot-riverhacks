from __future__ import annotations

import json
import os
from typing import Any

import anthropic

from data.loader import DataStore
from llm.prompts import REPORT_PROMPT, SYSTEM_PROMPT, TOOL_DEFINITIONS
from tools.actions import generate_daily_priorities
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

        # Get store name for context
        bu_row = store.business_units[store.business_units["bu_sk"] == bu_sk]
        self.store_name = bu_row.iloc[0]["bu_name"] if len(bu_row) > 0 else f"Store {bu_sk}"

    def _get_system_prompt(self) -> str:
        return (
            f"{SYSTEM_PROMPT}\n\n"
            f"## Current Context\n"
            f"- **Store**: {self.store_name}\n"
            f"- **Data as of**: {self.store.today.strftime('%A, %d %B %Y')}\n"
            f"- **Store ID (bu_sk)**: {self.bu_sk}\n"
        )

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

    def chat(self, user_message: str) -> str:
        """Send a user message and get a response. Maintains conversation history."""
        self.messages.append({"role": "user", "content": user_message})

        # Build messages for API call (full history)
        result = self._run_conversation(list(self.messages))

        self.messages.append({"role": "assistant", "content": result})
        return result

    def generate_report(self) -> str:
        """Generate the daily commercial briefing report."""
        # Use a fresh conversation for the report
        messages = [{"role": "user", "content": REPORT_PROMPT}]
        return self._run_conversation(messages)

    def reset_history(self) -> None:
        """Clear conversation history."""
        self.messages = []
