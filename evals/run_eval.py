"""
Evaluation runner for Hej Assistant.
Runs golden dataset questions through the RetailAgent, then uses Claude as a judge
to score responses on truthfulness, completeness, and other metrics.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data.loader import DataStore
from llm.agent import RetailAgent

JUDGE_MODEL = "claude-sonnet-4-6"
EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_DATASET = EVAL_DIR / "golden_dataset.json"
RESULTS_DIR = EVAL_DIR / "results"

JUDGE_SYSTEM = """You are an expert evaluator for a retail AI assistant used by IKEA store managers.
You will be given:
1. A QUESTION the store manager asked
2. The AI assistant's RESPONSE
3. GROUND TRUTH FACTS that should be reflected in the response
4. CRITICAL FACTS that must be present for a correct answer

Score the response on these dimensions (each 1-5):

**Truthfulness** (1-5): Are all stated facts correct? No hallucinated numbers or article names?
- 5: All facts match ground truth exactly
- 4: Minor rounding differences only
- 3: Mostly correct but 1-2 factual errors
- 2: Several factual errors or hallucinated data
- 1: Mostly wrong or fabricated

**Completeness** (1-5): Does the response cover all the critical facts?
- 5: All critical facts addressed
- 4: Most critical facts, missing 1
- 3: Covers about half
- 2: Misses most critical facts
- 1: Almost nothing relevant

**Relevance** (1-5): Does the response directly answer the question asked?
- 5: Directly and concisely answers the question
- 4: Answers the question with minor tangents
- 3: Partially answers, some off-topic content
- 2: Mostly off-topic
- 1: Does not address the question

**Actionability** (1-5): Does the response provide clear, actionable insights for a store manager?
- 5: Clear next steps or decisions the manager can act on
- 4: Somewhat actionable
- 3: Informational but not actionable
- 2: Vague or confusing
- 1: Not useful for decision-making

**Data Grounding** (1-5): Does the response cite specific data (numbers, article names, percentages)?
- 5: Rich with specific data points from the actual dataset
- 4: Several data points cited
- 3: Some data but also vague claims
- 2: Mostly vague, few specifics
- 1: No data cited

**Limitation Honesty** (1-5): For unanswerable questions, does it honestly say data is unavailable?
- 5: Clearly states what data is missing and why it can't fully answer
- 4: Acknowledges limitations
- 3: Partially acknowledges
- 2: Tries to answer without data, doesn't flag it
- 1: Fabricates an answer for unavailable data
(Score N/A for fully answerable questions — will be excluded from this metric)

Return your evaluation as JSON:
{
    "truthfulness": <1-5>,
    "completeness": <1-5>,
    "relevance": <1-5>,
    "actionability": <1-5>,
    "data_grounding": <1-5>,
    "limitation_honesty": <1-5 or null>,
    "overall": <1-5>,
    "explanation": "<2-3 sentence justification>",
    "errors_found": ["<list any factual errors found>"]
}
"""


def load_golden_dataset() -> list[dict]:
    with open(GOLDEN_DATASET) as f:
        return json.load(f)


def run_question(agent: RetailAgent, question: str) -> tuple[str, float]:
    """Run a single question through the agent, return response and latency."""
    agent.reset_history()
    start = time.time()
    try:
        response = agent.chat(question)
    except Exception as e:
        response = f"ERROR: {e}"
    latency = time.time() - start
    return response, latency


def judge_response(
    client: anthropic.Anthropic,
    question: str,
    response: str,
    ground_truth_facts: list[str],
    critical_facts: list[str],
    answerable: bool,
) -> dict:
    """Use Claude as a judge to score the response."""
    prompt = f"""## Question
{question}

## AI Assistant Response
{response}

## Ground Truth Facts
{chr(10).join(f'- {f}' for f in ground_truth_facts)}

## Critical Facts (must be present for correct answer)
{chr(10).join(f'- {f}' for f in critical_facts)}

## Question Answerable from Data: {"Yes" if answerable else "No — the data does NOT contain the information needed to fully answer this question"}

Please evaluate the response and return your scores as JSON only, no other text."""

    judge_response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1024,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = judge_response.content[0].text.strip()
    # Extract JSON from response
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "truthfulness": 0,
            "completeness": 0,
            "relevance": 0,
            "actionability": 0,
            "data_grounding": 0,
            "limitation_honesty": None,
            "overall": 0,
            "explanation": f"Judge response parse error: {text[:200]}",
            "errors_found": ["Judge response was not valid JSON"],
        }


def run_evaluation(bu_sk: int = 1, subset: list[str] | None = None):
    """Run the full evaluation pipeline."""
    print("=" * 70)
    print("HEJ ASSISTANT — EVALUATION PIPELINE")
    print("=" * 70)

    # Load data
    dataset = load_golden_dataset()
    if subset:
        dataset = [q for q in dataset if q["id"] in subset]
    print(f"\n📋 {len(dataset)} questions to evaluate")

    # Init agent
    print("🔧 Initializing DataStore and RetailAgent...")
    store = DataStore()
    agent = RetailAgent(store, bu_sk)
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    bu_row = store.business_units[store.business_units["bu_sk"] == bu_sk]
    store_name = bu_row.iloc[0]["bu_name"] if len(bu_row) > 0 else f"Store {bu_sk}"
    print(f"🏪 Store: {store_name} (bu_sk={bu_sk})")
    print(f"📅 Data date: {store.today.strftime('%Y-%m-%d')}")

    results = []
    total = len(dataset)

    for i, item in enumerate(dataset, 1):
        qid = item["id"]
        question = item["question"]
        print(f"\n{'─' * 60}")
        print(f"[{i}/{total}] {qid}: {question[:80]}...")

        # Run question through agent
        print("  ⏳ Running agent...")
        response, latency = run_question(agent, question)
        print(f"  ⏱️  Response in {latency:.1f}s ({len(response)} chars)")

        # Judge response
        print("  🧑‍⚖️ Judging response...")
        scores = judge_response(
            client,
            question,
            response,
            item["ground_truth_facts"],
            item["critical_facts"],
            item["answerable"],
        )
        print(f"  📊 Scores: T={scores.get('truthfulness', '?')} "
              f"C={scores.get('completeness', '?')} "
              f"R={scores.get('relevance', '?')} "
              f"A={scores.get('actionability', '?')} "
              f"D={scores.get('data_grounding', '?')} "
              f"O={scores.get('overall', '?')}")

        if scores.get("errors_found"):
            for err in scores["errors_found"]:
                print(f"  ❗ {err}")

        results.append({
            "id": qid,
            "question": question,
            "category": item["category"],
            "answerable": item["answerable"],
            "response": response,
            "latency_s": round(latency, 1),
            "response_length": len(response),
            **scores,
        })

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"eval_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Raw results saved to {results_file}")

    # Generate summary report
    generate_report(results, timestamp)

    return results


def generate_report(results: list[dict], timestamp: str):
    """Generate a summary report from evaluation results."""
    print("\n" + "=" * 70)
    print("EVALUATION REPORT")
    print("=" * 70)

    df = pd.DataFrame(results)
    metrics = ["truthfulness", "completeness", "relevance", "actionability", "data_grounding", "overall"]

    # Overall averages
    print("\n📊 OVERALL SCORES (1-5 scale)")
    print("─" * 40)
    for m in metrics:
        vals = pd.to_numeric(df[m], errors="coerce").dropna()
        if len(vals) > 0:
            avg = vals.mean()
            bar = "█" * int(avg) + "░" * (5 - int(avg))
            print(f"  {m:20s} {bar} {avg:.2f}")

    # Limitation honesty (only for unanswerable questions)
    unanswerable = df[~df["answerable"]]
    if len(unanswerable) > 0:
        lh_vals = pd.to_numeric(unanswerable["limitation_honesty"], errors="coerce").dropna()
        if len(lh_vals) > 0:
            avg = lh_vals.mean()
            bar = "█" * int(avg) + "░" * (5 - int(avg))
            print(f"  {'limitation_honesty':20s} {bar} {avg:.2f} (n={len(lh_vals)} unanswerable Qs)")

    # By category
    print("\n📂 SCORES BY CATEGORY")
    print("─" * 40)
    for cat in sorted(df["category"].unique()):
        cat_df = df[df["category"] == cat]
        overall_vals = pd.to_numeric(cat_df["overall"], errors="coerce").dropna()
        if len(overall_vals) > 0:
            print(f"  {cat:20s} overall={overall_vals.mean():.2f}  (n={len(cat_df)})")

    # Latency stats
    print(f"\n⏱️  LATENCY")
    print("─" * 40)
    print(f"  Mean:   {df['latency_s'].mean():.1f}s")
    print(f"  Median: {df['latency_s'].median():.1f}s")
    print(f"  Min:    {df['latency_s'].min():.1f}s")
    print(f"  Max:    {df['latency_s'].max():.1f}s")

    # Failures (overall <= 2)
    failures = df[pd.to_numeric(df["overall"], errors="coerce") <= 2]
    if len(failures) > 0:
        print(f"\n🔴 FAILED QUESTIONS (overall ≤ 2): {len(failures)}")
        print("─" * 40)
        for _, row in failures.iterrows():
            print(f"  {row['id']}: {row['question'][:60]}...")
            print(f"    → {row.get('explanation', 'No explanation')}")
    else:
        print(f"\n🟢 No failed questions (all scored > 2)")

    # Errors found
    all_errors = []
    for r in results:
        if r.get("errors_found"):
            for e in r["errors_found"]:
                all_errors.append(f"  {r['id']}: {e}")
    if all_errors:
        print(f"\n⚠️  FACTUAL ERRORS FOUND: {len(all_errors)}")
        print("─" * 40)
        for e in all_errors:
            print(e)

    # Pass rate
    passing = df[pd.to_numeric(df["overall"], errors="coerce") >= 3]
    pass_rate = len(passing) / len(df) * 100 if len(df) > 0 else 0
    print(f"\n{'=' * 40}")
    print(f"✅ PASS RATE (overall ≥ 3): {pass_rate:.0f}% ({len(passing)}/{len(df)})")
    print(f"{'=' * 40}")

    # Save report
    report_file = RESULTS_DIR / f"report_{timestamp}.txt"
    # Re-run report to file
    lines = []
    lines.append(f"Hej Assistant Evaluation Report — {timestamp}")
    lines.append(f"Questions: {len(df)}")
    lines.append(f"Pass rate: {pass_rate:.0f}%")
    lines.append("")
    for _, row in df.iterrows():
        lines.append(f"{row['id']} | {row['category']} | overall={row.get('overall', '?')} | "
                     f"T={row.get('truthfulness', '?')} C={row.get('completeness', '?')} "
                     f"R={row.get('relevance', '?')} A={row.get('actionability', '?')} "
                     f"D={row.get('data_grounding', '?')} | {row['latency_s']}s")
        lines.append(f"  Q: {row['question'][:80]}")
        lines.append(f"  → {row.get('explanation', '')}")
        lines.append("")
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Report saved to {report_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Hej Assistant evaluations")
    parser.add_argument("--store", type=int, default=1, help="Store bu_sk (default: 1 = Berlin)")
    parser.add_argument("--questions", nargs="*", help="Specific question IDs to run (e.g. Q01 Q05)")
    parser.add_argument("--quick", action="store_true", help="Run only 5 representative questions")
    args = parser.parse_args()

    subset = args.questions
    if args.quick:
        subset = ["Q01", "Q05", "Q14", "Q17", "Q03"]  # sales, declining, stock, risks, unanswerable

    run_evaluation(bu_sk=args.store, subset=subset)
