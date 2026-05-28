"""Evaluator agents for report and chat quality assurance.

Two-agent pattern:
- **Critic**: Reviews a draft and produces structured feedback (gaps, hallucinations, tone).
- **Evaluator**: Scores the final output on a rubric and decides pass/refine.

The report generator uses both (generate → critic → refine → evaluator).
The chat agent uses a lightweight evaluator only (to avoid latency).
"""

from __future__ import annotations

import json
import os

import anthropic

MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

REPORT_CRITIC_PROMPT = """\
You are a **senior IKEA retail operations reviewer**. You have just received a draft \
Daily Commercial Briefing written by an AI assistant for a store manager's morning huddle.

Your job is to **critique the draft** and return structured feedback so the assistant \
can improve it before it reaches the store manager.

## What to check

1. **Data completeness** — Does the report cover all required sections?
   - Sales Performance (7d, 30d, YTD vs forecast)
   - Stock & Availability (OOS count, top-seller risks)
   - Margin Health (overall %, problem areas)
   - Today's Priorities (ranked actions)
   - 3 Key Huddle Messages
   Missing section = critical gap.

2. **Actionability** — Every insight must lead to a "so what" or concrete action. \
   Flag any section that presents data without a recommendation.

3. **Number grounding** — Every claim must cite a specific number (€ amount, %, \
   unit count, article name). Flag vague statements like "sales are good" or \
   "some items are low".

4. **IKEA tone** — Should sound like a helpful co-worker, not a consulting report. \
   Flag overly formal or jargon-heavy language (except standard terms: HFB, PA, OSA, OOS).

5. **Hallucination risk** — Flag any article names, numbers, or claims that seem \
   fabricated or internally inconsistent (e.g., margin % doesn't match € figures).

6. **Priority logic** — Are the priorities correctly ranked by business impact? \
   OOS on a top seller should outrank minor margin concerns.

## Output format

Return a JSON object (no markdown fences):
{
  "overall_quality": "good" | "needs_revision" | "poor",
  "missing_sections": ["section names"],
  "issues": [
    {
      "severity": "critical" | "minor",
      "section": "which section",
      "issue": "what's wrong",
      "suggestion": "how to fix it"
    }
  ],
  "strengths": ["what's done well"],
  "revision_instructions": "If needs_revision: specific instructions for the rewrite. If good: empty string."
}
"""

REPORT_EVALUATOR_PROMPT = """\
You are a **quality gate** for IKEA store briefings. Score the report on these criteria \
and decide whether it is ready to show to a store manager.

## Scoring rubric (1-5 each)

| Criterion | 1 (Fail) | 3 (Acceptable) | 5 (Excellent) |
|---|---|---|---|
| **Completeness** | Missing 2+ sections | All sections present, some thin | Rich detail in every section |
| **Actionability** | No clear actions | Some actions, some vague | Every insight has a concrete next step |
| **Data accuracy** | Numbers seem wrong or vague | Numbers present, mostly cited | All claims backed by specific data |
| **Tone** | Too formal or robotic | Mostly IKEA-like | Reads like a great co-worker wrote it |
| **Prioritisation** | No ranking or wrong order | Reasonable ranking | Clearly impact-ordered with rationale |

## Output format

Return a JSON object (no markdown fences):
{
  "scores": {
    "completeness": <1-5>,
    "actionability": <1-5>,
    "data_accuracy": <1-5>,
    "tone": <1-5>,
    "prioritisation": <1-5>
  },
  "total_score": <sum out of 25>,
  "pass": true | false,
  "summary": "One-sentence quality verdict",
  "improvement_notes": "What would make this a 5/5 (for logging, not shown to user)"
}

A report passes if total_score >= 17 (no criterion below 3).
"""

CHAT_EVALUATOR_PROMPT = """\
You are a **quality checker** for an IKEA store manager chat assistant. You evaluate \
a single Q&A turn for correctness and helpfulness.

## Check these aspects

1. **Answers the question** — Does the response actually address what was asked? \
   Partial answers or tangents = flag.
2. **Data-grounded** — Are claims backed by specific numbers? Vague generalisations = flag.
3. **Actionable** — Does the response tell the manager what to *do*, not just what happened?
4. **Honest uncertainty** — If data is missing or ambiguous, does the response say so?
5. **Concise** — Managers are busy. Is the response appropriately concise?

## Output format

Return a JSON object (no markdown fences):
{
  "pass": true | false,
  "issues": ["list of problems, empty if pass"],
  "revision_hint": "If fail: one-sentence instruction for improvement. If pass: empty string."
}

Pass threshold: no critical issues (wrong data, doesn't answer, hallucinated content).
Minor issues (could be more concise, tone slightly off) should still pass.
"""


# ---------------------------------------------------------------------------
# Evaluator functions
# ---------------------------------------------------------------------------


def _call_llm(system_prompt: str, user_content: str) -> dict:
    """Make a single LLM call and parse JSON response."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))

    # Strip markdown code fences if the model wraps the JSON
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # Remove first line
    if text.endswith("```"):
        text = text.rsplit("\n", 1)[0]  # Remove last line
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse evaluator response", "raw": text}


def critique_report(draft_report: str) -> dict:
    """Run the critic agent on a draft report. Returns structured feedback."""
    return _call_llm(
        REPORT_CRITIC_PROMPT,
        f"## Draft Report to Review\n\n{draft_report}",
    )


def evaluate_report(final_report: str) -> dict:
    """Run the evaluator agent on the final report. Returns scores and pass/fail."""
    return _call_llm(
        REPORT_EVALUATOR_PROMPT,
        f"## Report to Evaluate\n\n{final_report}",
    )


def evaluate_chat_response(question: str, response: str) -> dict:
    """Run the lightweight evaluator on a chat Q&A turn."""
    return _call_llm(
        CHAT_EVALUATOR_PROMPT,
        f"## User Question\n{question}\n\n## Assistant Response\n{response}",
    )
