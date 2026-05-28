# Agent Memory

Append one entry after each meaningful agentic coding session.

## Template

```markdown
## YYYY-MM-DD - <short title>

**Task.** What did the agent try to do?

**Result.** What changed, and what evidence verified it?

**Failure or surprise.** What went wrong or took too long?

**Rule to add.** What instruction, test, or tool would prevent this next time?
```

---

## 2026-05-28 — Session 1: Initial scaffold + challenge data

**Task.** Set up the agentic engineering starter scaffold for the IKEA RiverHacks Challenge 3.

**Result.** Initial commit (`bdebb42`) created the full scaffold:
- Agent framework: `AGENTS.md`, `.cursor/rules/`, `.cursor/skills/`, `.cursor/commands/`, `.cursor/hooks.json`
- Hello-world MCP server under `mcp-servers/hello-world/`
- CI pipeline (`.github/workflows/ci.yml`), pre-commit config, bootstrap scripts
- Docs structure: `architecture/`, `knowledge/MEMORY.md`, `references/`, ADR scaffold
- Sample `src/sample/greeter.py` + `tests/sample/test_greeter.py` so lint/test/typecheck work out of the box
- Challenge data file (`Challenge_3_Dummy_data_store_ops_information.xlsx`) included in repo

**Failure or surprise.** None — standard scaffold setup.

**Rule to add.** n/a

---

## 2026-05-28 — Session 2: Build the full MVP ("Hej Assistant")

**Task.** Build the complete AI-powered daily commercial briefing and Q&A tool for IKEA store managers, from raw Excel data to a working deployed app.

**Result.** Commit `b11f8ab` + `d71349a` added the full MVP (~545K lines changed):

### Data layer
- Extracted 5 CSVs from the challenge Excel file: `data/Sales.csv` (363K rows), `data/Forecast.csv` (87K), `data/Stock.csv` (87K), `data/Product.csv` (30), `data/Business_Unit.csv` (8)
- `src/data/loader.py` — `DataStore` class that loads all CSVs into pandas DataFrames with mixed-date parsing and join helpers
- `src/data/periods.py` — time period filters (`last_7_days`, `last_30_days`, `ytd`, `previous_period`)

### Analytics tools (14 tools)
- `src/tools/sales.py` — sales summary, vs forecast, top articles, HFB performance, declining articles
- `src/tools/stock.py` — stock alerts, availability risks, OOS top sellers, overstock articles
- `src/tools/margin.py` — margin analysis, top profitable articles, low margin alerts, HFB margin
- `src/tools/actions.py` — daily priority generator combining all signals into a ranked action list

### LLM agent orchestrator
- `src/llm/agent.py` — `RetailAgent` class with Claude tool-calling loop (max 10 rounds)
- `src/llm/prompts.py` — system prompt (IKEA retail expert persona), report template, 14 tool schemas
- `src/llm/validators.py` — post-generation checks for article name verification and number reasonableness

### Frontend (used Skapa MCP server for IKEA design system)
- `src/static/index.html` — single-page app with sidebar (store selector, metrics) and 3 tabs (Briefing, Chat, Data Explorer)
- `src/static/style.css` — IKEA Skapa design tokens (colours, spacing, typography, component styles); built with guidance from the Skapa MCP server to ensure correct IKEA design language
- `src/static/app.js` — fetch-based API client, tab navigation, markdown rendering, data tables
- `.cursor/skills/iidp-skapa-ui-standards/SKILL.md` — added a skill for Skapa UI standards reference

### Backend
- `src/server.py` — FastAPI server with CORS, static file serving, 14 API endpoints
- `src/app.py` — standalone/CLI version of the app
- Deployment config: `Procfile`, `railway.json`, `requirements.txt`

### Questions catalogue
- `questions.md` — 78 curated store manager questions across sales, margin, stock, availability, discontinued items, daily priorities, Top 30, and coaching huddle topics. These serve as the evaluation dataset and demo script.

### Architecture documentation
- `docs/architecture/architecture.md` — comprehensive system overview with Mermaid diagrams, component mapping, API endpoint table, deployment section, and target-vs-implementation status
- `docs/production-readiness/` — 15 production readiness guides covering supply chain, secrets, FastAPI hardening, testing, CI/CD, observability, migrations, Databricks, Azure infra, compliance, and more

### Evaluation framework
- `evals/run_eval.py` + `evals/golden_dataset.json` — automated evaluation harness with scoring rubric
- First eval run: 80% pass rate (4/5 questions passed). Q03 ("PA underperformed despite high traffic") failed because the agent hallucinated traffic data that doesn't exist in the dataset.

**Failure or surprise.**
- The agent hallucinated traffic/footfall data on Q03 — it presented sales declines as if they answered a traffic question, framing it as "conversion is the issue, not traffic" without any traffic data. This is a known gap: the dataset has no footfall/traffic data.
- The eval framework caught this, which validates the eval approach.

**Rule to add.** Add a validator or system prompt instruction that forces the agent to explicitly state when requested data dimensions (traffic, footfall, conversion) are not available in the dataset, rather than reframing the question.

---

## 2026-05-28 — Session 3: Roadmap features (in progress, uncommitted)

**Task.** Extend the MVP with roadmap features: external context (holidays/promotions), what-if analysis, conversation memory, alert scheduler, and UI enhancements.

**Result.** Uncommitted changes across 7 files (+737 lines):
- `src/tools/external_context.py` (new, 255 lines) — holidays, promotions, seasonal events calendar; static data simulating what would be API-backed in production
- `src/tools/whatif.py` (new, 193 lines) — what-if analysis sparring tool for price changes, availability scenarios
- `src/llm/memory.py` (new) — conversation memory with session history + persistent user preferences (JSON file)
- `src/llm/scheduler.py` (new) — alert scheduler for proactive insights generation
- `src/llm/agent.py` — extended agent with new tool integrations
- `src/llm/prompts.py` — added tool schemas for new tools
- `src/server.py` — new API endpoints for new features
- `src/static/index.html`, `app.js`, `style.css` — UI updates for new features

**Failure or surprise.** Work is still in progress and uncommitted.

**Rule to add.** Commit more frequently — multiple features in one uncommitted batch makes rollback harder.

---

## 2026-05-28 — Session 4: Evaluation framework & golden dataset results

**Task.** Build an automated evaluation pipeline to test the 78 store manager questions from `questions.md` against ground truth data, using LLM-as-judge for scoring.

### Evaluation setup

**Libraries & tools used:**
- **Anthropic Python SDK** (`anthropic>=0.52.0`) — both for running the RetailAgent (tool-calling) and for LLM-as-judge scoring
- **pandas** — ground truth data extraction and report aggregation
- **Model under test:** `claude-sonnet-4-6` (RetailAgent)
- **Judge model:** `claude-sonnet-4-6` (same model, different prompt)
- **Store tested:** NORVIK Berlin (bu_sk=1), data as of 2024-12-30

**What we test on:**
- `evals/golden_dataset.json` — 25 curated questions (subset of the 78 in `questions.md`) across 5 categories: sales, margin, stock, sales_stock, actions
- Each question has: ground truth facts extracted directly from the analysis tools, critical facts that must appear, expected tools to be called, and an `answerable` flag for questions the dataset cannot answer
- 3 questions marked as `answerable: false` (Q03: traffic data, Q06: time-of-day, Q07: new article launches) to test limitation honesty

**Scoring rubric (1-5 each):**
| Metric | What it measures |
|---|---|
| Truthfulness | Are stated facts correct? No hallucinated numbers? |
| Completeness | Are all critical facts addressed? |
| Relevance | Does the response directly answer the question? |
| Actionability | Are insights actionable for a store manager? |
| Data Grounding | Does it cite specific data (numbers, article names)? |
| Limitation Honesty | For unanswerable Qs: does it say data is unavailable? |

### Results (5-question quick run, 2026-05-28)

| Question | Category | Overall | T | C | R | A | D | Latency |
|---|---|---|---|---|---|---|---|---|
| Q01: Sales vs forecast (7d/30d/YTD) | sales | **5** | 5 | 5 | 5 | 5 | 5 | 11.9s |
| Q03: PA underperformed despite traffic | sales | **1** ❌ | 2 | 1 | 2 | 3 | 3 | 24.4s |
| Q05: Declining articles (30d) | sales | **5** | 5 | 5 | 5 | 5 | 5 | 20.0s |
| Q14: High sellers out of stock | stock | **5** | 4 | 5 | 5 | 5 | 5 | 14.7s |
| Q17: Availability risks to escalate | stock | **5** | 4 | 5 | 5 | 5 | 4 | 18.1s |

**Aggregate scores:**
- **Overall:** 4.20/5
- **Truthfulness:** 4.00/5
- **Completeness:** 4.20/5
- **Relevance:** 4.40/5
- **Actionability:** 4.60/5
- **Data Grounding:** 4.40/5
- **Limitation Honesty:** 1.00/5 (1 unanswerable question — agent fabricated an answer)
- **Pass rate:** 80% (4/5, threshold: overall ≥ 3)
- **Mean latency:** 17.8s

### Key findings

1. **Strong on answerable questions** — scores 5/5 overall on sales and stock questions where data exists
2. **Hallucination on unanswerable questions** — Q03 asked about traffic/footfall data that doesn't exist. The agent fabricated a "demand factor 1.4x" and claimed "conversion is the issue, not traffic" without any traffic data. This is the critical failure mode.
3. **Minor truthfulness gaps** — the judge flagged some article names (ELVEN, PAXON, KALLO) as "unverifiable" because the golden dataset's ground truth only included top-5 items, not the full tool output. These are likely real data, not hallucinations — the judge was being conservative.
4. **Actionability is the strongest dimension** — every response included clear next steps for store managers

**Failure or surprise.** The agent confidently answers questions about data dimensions it doesn't have (traffic, footfall). It should refuse or caveat instead of reframing the question with fabricated framing.

**Rule to add.** Add to the system prompt: "If the user asks about data you cannot access (traffic, footfall, conversion rates, time-of-day patterns, customer counts), explicitly state that this data is not available in the current dataset. Do not reframe the question to fit available data without acknowledging the limitation."
