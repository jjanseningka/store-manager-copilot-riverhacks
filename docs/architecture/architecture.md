# Hej Assistant — Architecture

> An AI-powered daily commercial briefing and Q&A tool for IKEA store managers.

## Target Architecture

![Target Architecture](../../assets/architecture-target.png)

The diagram above shows the full target vision. Below we map each component to what is implemented today and what remains on the roadmap.

---

## Context

**Hej Assistant** is a GenAI prototype built for the IKEA RiverHacks hackathon. It gives IKEA store managers a single interface to:

1. **Get a daily AI-generated commercial briefing** — sales performance, stock health, margin analysis, and prioritised actions.
2. **Ask follow-up questions** — conversational Q&A backed by real store data and Claude tool-calling.
3. **Explore data** — interactive tables for top articles, HFB performance, stock alerts, declining articles, and more.

The system runs as a single deployable unit on Railway (FastAPI + static HTML) and calls the Anthropic Claude API for LLM capabilities.

---

## System Overview

```mermaid
flowchart TD
    subgraph Frontend["Store Manager Interface"]
        UI[HTML + CSS + JS]
        TABS["3 Tabs: Briefing · Chat · Data Explorer"]
        SKAPA["Skapa Design System tokens"]
    end

    subgraph Backend["FastAPI Server"]
        API[REST API endpoints]
        SESSIONS[Session Manager]
    end

    subgraph Orchestrator["LLM Agent Orchestrator"]
        AGENT[RetailAgent]
        TOOLS[14 Tool Definitions]
        PROMPT[System Prompt + IKEA Tone]
        VALID[Response Validators]
    end

    subgraph Analytics["Analytics Tools"]
        SALES[Sales Analysis]
        STOCK[Stock Analysis]
        MARGIN[Margin Analysis]
        ACTIONS[Priority Generator]
    end

    subgraph DataLayer["Data Layer"]
        LOADER[DataStore]
        PERIODS[Period Filters]
        CSV[(CSV Files)]
    end

    subgraph External["External Services"]
        CLAUDE[Claude Sonnet 4.6 API]
    end

    UI --> API
    API --> AGENT
    API --> SALES & STOCK & MARGIN & ACTIONS
    AGENT -->|tool-calling loop| TOOLS
    TOOLS --> SALES & STOCK & MARGIN & ACTIONS
    AGENT <-->|messages| CLAUDE
    SALES & STOCK & MARGIN & ACTIONS --> LOADER
    LOADER --> PERIODS
    LOADER --> CSV
    AGENT --> VALID
```

---

## Components

### Layer 1 — Store Manager Interface

| Component | Path | Description |
|---|---|---|
| HTML page | `src/static/index.html` | Single-page app with sidebar (store selector, metrics) and 3 tabs |
| Skapa CSS | `src/static/style.css` | IKEA Skapa design tokens — colours, spacing, typography, component styles |
| App logic | `src/static/app.js` | Fetch-based API client, tab navigation, markdown rendering, data tables |

**Features:**
- Store selector dropdown (8 IKEA stores)
- Snapshot cards (7d/30d sales, stock health, margin)
- AI report generation with PDF export
- Chat with suggestion chips and session management
- Data explorer with 6 views and period filters

### Layer 2 — FastAPI Server

| Component | Path | Description |
|---|---|---|
| Server | `src/server.py` | FastAPI app with CORS, static file serving, all API endpoints |

**API Endpoints:**

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check + data date |
| `GET` | `/api/stores` | List all stores |
| `GET` | `/api/snapshot/{bu_sk}` | KPI snapshot (sales, stock, margin) |
| `GET` | `/api/top-articles/{bu_sk}` | Top-selling articles |
| `GET` | `/api/hfb-performance/{bu_sk}` | HFB performance breakdown |
| `GET` | `/api/stock-alerts/{bu_sk}` | Stock status (OOS, low, healthy) |
| `GET` | `/api/availability-risks/{bu_sk}` | Burn-rate based OOS predictions |
| `GET` | `/api/declining-articles/{bu_sk}` | Week-over-week declining articles |
| `GET` | `/api/daily-priorities/{bu_sk}` | AI-ranked daily action list |
| `GET` | `/api/margin/{bu_sk}` | Margin analysis |
| `POST` | `/api/report` | Generate AI daily briefing |
| `POST` | `/api/chat` | Conversational Q&A |
| `POST` | `/api/chat/reset` | Reset chat session |
| `POST` | `/api/export-pdf` | Export briefing as PDF |

### Layer 3 — LLM Agent Orchestrator

| Component | Path | Description |
|---|---|---|
| Agent | `src/llm/agent.py` | `RetailAgent` class — manages Claude conversation with tool-calling loop (max 10 rounds) |
| Prompts | `src/llm/prompts.py` | System prompt (IKEA retail expert persona), report template, 14 tool schemas |
| Validators | `src/llm/validators.py` | Post-generation checks: article name verification, number reasonableness |

**How the agent works:**

1. User sends a message (or report request)
2. `RetailAgent` sends the message + tool definitions to Claude
3. Claude decides which tools to call (e.g., `get_sales_summary`, `get_stock_alerts`)
4. Agent executes tools against real store data, returns results to Claude
5. Claude synthesises a natural-language response using IKEA tone of voice
6. Validators check the response for accuracy
7. Response returned to the frontend

**Tool inventory (14 tools):**

| Tool | Module | What it analyses |
|---|---|---|
| `get_sales_summary` | `sales.py` | 7d, 30d, YTD sales overview |
| `get_sales_vs_forecast` | `sales.py` | Actual vs forecast comparison |
| `get_top_articles` | `sales.py` | Top N by sales or profit |
| `get_hfb_performance` | `sales.py` | HFB breakdown with WoW growth |
| `get_declining_articles` | `sales.py` | Week-over-week decliners |
| `get_stock_alerts` | `stock.py` | OOS / low / healthy counts |
| `get_availability_risks` | `stock.py` | Burn rate → days until OOS |
| `get_oos_top_sellers` | `stock.py` | Top sellers with stock issues |
| `get_overstock_articles` | `stock.py` | Overstocked items |
| `get_margin_analysis` | `margin.py` | Gross margin breakdown |
| `get_top_profitable_articles` | `margin.py` | Highest margin articles |
| `get_low_margin_alerts` | `margin.py` | Below-threshold margin items |
| `get_hfb_margin_analysis` | `margin.py` | Margin by HFB |
| `generate_daily_priorities` | `actions.py` | Ranked action list combining all signals |

### Layer 4 — Data Layer

| Component | Path | Description |
|---|---|---|
| DataStore | `src/data/loader.py` | Loads 5 CSVs, provides join helpers, mixed-date parsing |
| Periods | `src/data/periods.py` | Time filters: `last_7_days`, `last_30_days`, `ytd`, `previous_period` |

**Data sources (CSV):**

| File | Rows | Key columns |
|---|---|---|
| `data/Sales.csv` | ~363K | transaction_date, item_no, bu_sk, qty, net_amount, margin |
| `data/Forecast.csv` | ~87K | forecast_date, item_no, bu_sk, forecasted_qty |
| `data/Stock.csv` | ~87K | snapshot_date, item_sk, bu_sk, available_stock, demand_stock |
| `data/Product.csv` | ~30 | item_no, item_sk, series, description, colour, HFB |
| `data/Business_Unit.csv` | 8 | bu_sk, bu_name, bu_short_name, city |

**Date range:** 2024-01-01 to 2024-12-30 · `today` = max date in sales data

---

## Architecture Mapping: Target → Implementation

| Target Component | Status | Implementation |
|---|---|---|
| **Store manager interface** | ✅ Built | `src/static/` — HTML/CSS/JS with Skapa design, 3 tabs |
| **LLM agent orchestrator** | ✅ Built | `src/llm/agent.py` — Claude tool-calling with 14 tools |
| **Q&A engine** | ✅ Built | `/api/chat` — conversational Q&A with store context |
| **Analysis sparring** | ⚠️ Partial | Tool-calling supports multi-step analysis; no what-if scenarios yet |
| **Proactive insights** | ⚠️ Partial | `daily-priorities` endpoint generates alerts; not auto-surfaced yet |
| **Conversation memory** | ⚠️ Partial | In-memory session history; no persistent preferences |
| **Analytics tools** | ✅ Built | `src/tools/` — sales, stock, margin, actions modules |
| **Alert scheduler** | ❌ Roadmap | No background scheduler; alerts are on-demand only |
| **Forecast data store** | ✅ Built | CSV-based with demand, accuracy via forecast vs actual |
| **Vector knowledge base** | ❌ Roadmap | No embeddings or document retrieval |
| **External context** | ❌ Roadmap | No holidays, promotions, or weather integration |

---

## Deployment

```
Railway (Nixpacks)
├── Procfile          → cd src && uvicorn server:app --host 0.0.0.0 --port $PORT
├── railway.json      → health check on /api/health
├── requirements.txt  → fastapi, uvicorn, anthropic, pandas, fpdf2, python-dotenv
└── .python-version   → 3.11
```

**Environment variables:**

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for LLM features |
| `PORT` | Auto | Set by Railway |

---

## Design Decisions

- **Single deployable unit** — no microservices; FastAPI serves both API and static files for simplicity at hackathon scale.
- **CSV over database** — data is small (< 1M rows total), pre-loaded at startup into pandas DataFrames for fast analysis.
- **Tool-calling over RAG** — Claude decides which analysis to run based on the user's question, rather than retrieving from a vector store. More deterministic and auditable.
- **Skapa design tokens only** — we use IKEA's CSS variables directly instead of the `@ingka` npm packages (which require internal registry access).
- **Session-scoped chat** — conversation history resets on store change or page reload. No persistent storage needed for a demo.

---

## Roadmap (Post-Hackathon)

| Priority | Feature | Description |
|---|---|---|
| 🔴 High | **Proactive alerts** | Auto-surface critical insights on page load (OOS top sellers, forecast misses) |
| 🔴 High | **What-if analysis** | "What if we reprice KALLAX by 10%?" — margin/volume simulation tool |
| 🟡 Medium | **Alert scheduler** | Background job that generates morning briefings before store opens |
| 🟡 Medium | **Persistent memory** | Remember manager preferences, past conversations, store-specific context |
| 🟢 Low | **Vector knowledge base** | Embed SOPs, playbooks, corporate guidelines for retrieval |
| 🟢 Low | **External context** | Holiday calendar, promotion schedule, weather data for demand context |
