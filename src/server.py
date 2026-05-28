from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from data.loader import DataStore
from llm.agent import RetailAgent
from llm.memory import get_memory
from llm.scheduler import AlertScheduler
from llm.validators import validate_article_references, validate_numbers_reasonable
from tools.actions import generate_daily_priorities
from tools.external_context import get_store_context
from tools.margin import (
    get_margin_analysis,
)
from tools.sales import (
    get_declining_articles,
    get_hfb_performance,
    get_sales_vs_forecast,
    get_top_articles,
)
from tools.stock import get_availability_risks, get_stock_alerts
from tools.whatif import whatif_availability_improvement, whatif_demand_surge, whatif_price_change

# ---------------------------------------------------------------------------
# Data loading (singleton)
# ---------------------------------------------------------------------------
store = DataStore()
scheduler = AlertScheduler(store, refresh_interval_minutes=30)
memory = get_memory()


# ---------------------------------------------------------------------------
# App lifespan — start/stop scheduler
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await scheduler.start()
    yield
    await scheduler.stop()


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Hej Assistant — IKEA Store Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Session management for chat agents
# ---------------------------------------------------------------------------
_sessions: dict[str, RetailAgent] = {}


def _get_or_create_agent(session_id: str, bu_sk: int) -> RetailAgent:
    key = f"{session_id}:{bu_sk}"
    if key not in _sessions:
        agent = RetailAgent(store, bu_sk)
        agent.session_id = session_id
        _sessions[key] = agent
    return _sessions[key]


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: str
    bu_sk: int
    message: str


class ChatResponse(BaseModel):
    response: str
    warnings: list[str]
    evaluation: dict | None = None


class ReportRequest(BaseModel):
    bu_sk: int


class ReportResponse(BaseModel):
    report: str
    warnings: list[str]
    evaluation: dict | None = None


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "data_date": str(store.today.date())}


@app.get("/api/stores")
def list_stores():
    return store.store_names()


@app.get("/api/snapshot/{bu_sk}")
def get_snapshot(bu_sk: int):
    """Quick data snapshot for a store — no LLM needed."""
    try:
        s7 = get_sales_vs_forecast(store, bu_sk, "7d")
        s30 = get_sales_vs_forecast(store, bu_sk, "30d")
        alerts = get_stock_alerts(store, bu_sk)
        margin = get_margin_analysis(store, bu_sk, "7d")
        return {
            "sales_7d": s7,
            "sales_30d": s30,
            "stock_alerts": {
                "out_of_stock_count": alerts["out_of_stock_count"],
                "low_stock_count": alerts["low_stock_count"],
                "healthy_count": alerts["healthy_count"],
                "total_items": alerts["total_items"],
            },
            "margin_7d": margin,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/top-articles/{bu_sk}")
def api_top_articles(bu_sk: int, period: str = "7d", n: int = 10, metric: str = "sales"):
    return get_top_articles(store, bu_sk, period, n, metric)


@app.get("/api/hfb-performance/{bu_sk}")
def api_hfb_performance(bu_sk: int, period: str = "7d"):
    return get_hfb_performance(store, bu_sk, period)


@app.get("/api/stock-alerts/{bu_sk}")
def api_stock_alerts(bu_sk: int):
    return get_stock_alerts(store, bu_sk)


@app.get("/api/availability-risks/{bu_sk}")
def api_availability_risks(bu_sk: int):
    return get_availability_risks(store, bu_sk)


@app.get("/api/daily-priorities/{bu_sk}")
def api_daily_priorities(bu_sk: int):
    return generate_daily_priorities(store, bu_sk)


@app.get("/api/margin/{bu_sk}")
def api_margin(bu_sk: int, period: str = "7d"):
    return get_margin_analysis(store, bu_sk, period)


@app.get("/api/declining-articles/{bu_sk}")
def api_declining_articles(bu_sk: int):
    return get_declining_articles(store, bu_sk)


# ---------------------------------------------------------------------------
# New: Proactive insights, external context, what-if
# ---------------------------------------------------------------------------


@app.get("/api/insights/{bu_sk}")
def api_insights(bu_sk: int):
    """Get auto-generated proactive insights (cached by scheduler)."""
    return scheduler.get_insights(bu_sk)


@app.get("/api/external-context/{bu_sk}")
def api_external_context(bu_sk: int):
    """Get external context: holidays, promotions, seasonal patterns."""
    return get_store_context(store.today, bu_sk)


class WhatIfPriceRequest(BaseModel):
    item_no: int
    price_change_pct: float
    period: str = "30d"


class WhatIfDemandRequest(BaseModel):
    demand_increase_pct: float
    period: str = "7d"


@app.post("/api/whatif/price/{bu_sk}")
def api_whatif_price(bu_sk: int, req: WhatIfPriceRequest):
    return whatif_price_change(store, bu_sk, req.item_no, req.price_change_pct, req.period)


@app.get("/api/whatif/availability/{bu_sk}")
def api_whatif_availability(bu_sk: int):
    return whatif_availability_improvement(store, bu_sk)


@app.post("/api/whatif/demand/{bu_sk}")
def api_whatif_demand(bu_sk: int, req: WhatIfDemandRequest):
    return whatif_demand_surge(store, bu_sk, req.demand_increase_pct, req.period)


@app.get("/api/memory/preferences/{bu_sk}")
def api_get_preferences(bu_sk: int):
    return memory.get_preferences(f"store_{bu_sk}")


@app.post("/api/memory/preferences/{bu_sk}")
def api_set_preference(bu_sk: int, key: str, value: str):
    memory.set_preference(f"store_{bu_sk}", key, value)
    return {"status": "ok"}


@app.post("/api/report", response_model=ReportResponse)
def generate_report(req: ReportRequest):
    """Generate daily commercial briefing using Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    try:
        agent = RetailAgent(store, req.bu_sk)
        report, evaluation = agent.generate_report()
        warnings = validate_article_references(report, store)
        warnings += validate_numbers_reasonable(report)
        return ReportResponse(report=report, warnings=warnings, evaluation=evaluation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Chat with the retail assistant."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    try:
        agent = _get_or_create_agent(req.session_id, req.bu_sk)
        response, evaluation = agent.chat(req.message)
        warnings = validate_article_references(response, store)
        return ChatResponse(response=response, warnings=warnings, evaluation=evaluation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/reset")
def reset_chat(session_id: str, bu_sk: int):
    key = f"{session_id}:{bu_sk}"
    if key in _sessions:
        del _sessions[key]
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------
@app.post("/api/export-pdf")
def export_pdf(req: ReportRequest):
    """Export the daily report as PDF."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    try:
        agent = RetailAgent(store, req.bu_sk)
        report, _ = agent.generate_report()

        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=10)

        for line in report.split("\n"):
            clean = line.replace("#", "").replace("**", "").replace("*", "")
            clean = clean.replace("🔴", "[!]").replace("🟡", "[~]").replace("🟢", "[OK]")
            clean = clean.replace("📊", "").replace("📦", "").replace("💰", "")
            clean = clean.replace("⚡", "").replace("→", "->")
            if clean.strip():
                pdf.multi_cell(0, 6, clean.encode("latin-1", "replace").decode("latin-1"))

        pdf_bytes = pdf.output()
        return Response(
            content=bytes(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=daily_briefing_{store.today.strftime('%Y-%m-%d')}.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Serve static frontend
# ---------------------------------------------------------------------------
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
