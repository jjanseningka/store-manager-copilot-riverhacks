"""Proactive insights engine.

Auto-surfaces critical alerts and opportunities without the manager asking.
Runs on store load and can be triggered by the alert scheduler.
"""

from __future__ import annotations

from typing import Any

from data.loader import DataStore
from tools.external_context import get_store_context
from tools.margin import get_margin_analysis
from tools.sales import get_declining_articles, get_sales_vs_forecast
from tools.stock import get_availability_risks, get_oos_top_sellers, get_stock_alerts


def generate_proactive_insights(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Generate auto-surfaced insights combining all signals.

    Returns categorised insights with severity and recommended actions.
    Each insight is self-contained and actionable.
    """
    insights: list[dict[str, Any]] = []

    # --- Sales insights ---
    try:
        sales_7d = get_sales_vs_forecast(store, bu_sk, "7d")
        gap = sales_7d.get("gap_percent", 0)

        if gap < -10:
            insights.append(
                {
                    "type": "alert",
                    "severity": "critical",
                    "category": "sales",
                    "title": f"Sales {abs(gap)}% below forecast",
                    "message": (
                        f"7-day sales are significantly below forecast "
                        f"({sales_7d['actual_sales_units']} units vs {round(sales_7d['forecast_units'])} forecasted). "
                        f"Revenue gap: €{abs(round(sales_7d.get('gap_units', 0) * (sales_7d.get('actual_sales_net_euro', 0) / max(sales_7d.get('actual_sales_units', 1), 1)), 0)):,.0f}."
                    ),
                    "action": "Review floor plans, staffing, and product visibility for top sellers.",
                    "icon": "📉",
                }
            )
        elif gap < -5:
            insights.append(
                {
                    "type": "alert",
                    "severity": "warning",
                    "category": "sales",
                    "title": f"Sales {abs(gap)}% below forecast",
                    "message": f"Moderate gap — {round(abs(sales_7d.get('gap_units', 0)))} units behind target this week.",
                    "action": "Focus floor presence on top-selling articles during peak hours.",
                    "icon": "📊",
                }
            )
        elif gap > 5:
            insights.append(
                {
                    "type": "opportunity",
                    "severity": "positive",
                    "category": "sales",
                    "title": f"Sales {gap}% above forecast!",
                    "message": f"Great momentum — {round(sales_7d.get('gap_units', 0))} extra units sold this week.",
                    "action": "Ensure stock replenishment keeps up with demand. Celebrate with the team!",
                    "icon": "🎉",
                }
            )
    except Exception:
        pass

    # --- Stock insights ---
    try:
        stock = get_stock_alerts(store, bu_sk)
        oos_count = stock.get("out_of_stock_count", 0)

        if oos_count > 5:
            oos_names = [
                f"{x.get('series', '')} {x.get('description', '')}"
                for x in stock.get("out_of_stock", [])[:3]
            ]
            insights.append(
                {
                    "type": "alert",
                    "severity": "critical",
                    "category": "availability",
                    "title": f"{oos_count} articles out of stock",
                    "message": f"Including: {', '.join(oos_names)}. Every OOS item is a missed sale.",
                    "action": "Prioritise replenishment orders. Check if alternatives can be cross-merchandised.",
                    "icon": "🔴",
                }
            )
        elif oos_count > 0:
            insights.append(
                {
                    "type": "alert",
                    "severity": "warning",
                    "category": "availability",
                    "title": f"{oos_count} article(s) out of stock",
                    "message": "Monitor replenishment and check delivery schedules.",
                    "action": "Verify pending orders and expected delivery dates.",
                    "icon": "🟡",
                }
            )
    except Exception:
        pass

    # --- Availability risks ---
    try:
        risks = get_availability_risks(store, bu_sk)
        critical_risks = [r for r in risks.get("risks", []) if r.get("severity") == "critical"]
        if critical_risks:
            names = [
                f"{r.get('series', '')} {r.get('description', '')}" for r in critical_risks[:3]
            ]
            insights.append(
                {
                    "type": "alert",
                    "severity": "critical",
                    "category": "availability",
                    "title": f"{len(critical_risks)} items will run out in 2 days",
                    "message": f"At current sell-through: {', '.join(names)}.",
                    "action": "Place emergency replenishment orders. Consider substitution displays.",
                    "icon": "⏰",
                }
            )
    except Exception:
        pass

    # --- Top sellers at risk ---
    try:
        oos_sellers = get_oos_top_sellers(store, bu_sk)
        if oos_sellers.get("at_risk_count", 0) > 0:
            insights.append(
                {
                    "type": "alert",
                    "severity": "critical",
                    "category": "revenue",
                    "title": f"{oos_sellers['at_risk_count']} top sellers have stock issues",
                    "message": "Your highest-revenue products are affected by availability problems.",
                    "action": "Protect top sellers first — they drive disproportionate revenue.",
                    "icon": "💰",
                }
            )
    except Exception:
        pass

    # --- Margin insights ---
    try:
        margin = get_margin_analysis(store, bu_sk, "7d")
        margin_pct = margin.get("margin_percent", 0)
        if margin_pct < 10:
            insights.append(
                {
                    "type": "alert",
                    "severity": "critical",
                    "category": "margin",
                    "title": f"Margin critically low at {margin_pct}%",
                    "message": "Gross margin is well below target. Check for heavy discounting or pricing errors.",
                    "action": "Review active markdowns and escalate pricing concerns.",
                    "icon": "⚠️",
                }
            )
        elif margin_pct < 20:
            insights.append(
                {
                    "type": "alert",
                    "severity": "warning",
                    "category": "margin",
                    "title": f"Margin below target at {margin_pct}%",
                    "message": "Consider pushing higher-margin alternatives and reviewing discount strategies.",
                    "action": "Brief team on margin-friendly upsell opportunities.",
                    "icon": "💸",
                }
            )
    except Exception:
        pass

    # --- Declining articles ---
    try:
        declining = get_declining_articles(store, bu_sk, n=5)
        articles = declining.get("articles", [])
        if len(articles) >= 3:
            names = [f"{a.get('series', '')} {a.get('description', '')}" for a in articles[:3]]
            worst_change = articles[0].get("change_pct", 0) if articles else 0
            insights.append(
                {
                    "type": "alert",
                    "severity": "warning",
                    "category": "momentum",
                    "title": f"{len(articles)} articles losing momentum",
                    "message": f"Biggest decline: {names[0]} at {worst_change}%. Also declining: {', '.join(names[1:])}.",
                    "action": "Check floor positioning and consider promotional boosts.",
                    "icon": "📉",
                }
            )
    except Exception:
        pass

    # --- External context insights ---
    try:
        context = get_store_context(store.today, bu_sk)
        events = context.get("upcoming_events", [])
        promos = context.get("active_promotions", [])
        seasonal = context.get("seasonal", {})

        # Upcoming high-impact events
        high_impact_events = [
            e for e in events if e.get("impact") == "high" and e.get("days_until", 99) <= 7
        ]
        if high_impact_events:
            event_names = [f"{e['name']} (in {e['days_until']}d)" for e in high_impact_events]
            insights.append(
                {
                    "type": "opportunity",
                    "severity": "info",
                    "category": "events",
                    "title": f"High-impact event in {high_impact_events[0]['days_until']} days",
                    "message": f"Upcoming: {', '.join(event_names)}. Expect traffic changes.",
                    "action": "Ensure seasonal displays are ready and stock levels are adequate.",
                    "icon": "📅",
                }
            )

        # Active promotions
        if promos:
            promo_names = [f"{p['name']} ({p['discount_pct']}% off)" for p in promos]
            insights.append(
                {
                    "type": "opportunity",
                    "severity": "info",
                    "category": "promotions",
                    "title": f"{len(promos)} active promotion(s)",
                    "message": f"Running now: {', '.join(promo_names)}.",
                    "action": "Verify promo displays are prominent and stock is allocated.",
                    "icon": "🏷️",
                }
            )

        # Seasonal demand
        if seasonal.get("demand_factor", 1.0) >= 1.2:
            insights.append(
                {
                    "type": "opportunity",
                    "severity": "positive",
                    "category": "seasonal",
                    "title": f"High demand season: {seasonal.get('trend', '')}",
                    "message": f"Demand factor is {seasonal['demand_factor']}x — expect above-average traffic.",
                    "action": "Maximise floor coverage and staff key departments.",
                    "icon": "🔥",
                }
            )
    except Exception:
        pass

    # Sort: critical first, then warning, then info/positive
    severity_order = {"critical": 0, "warning": 1, "info": 2, "positive": 3}
    insights.sort(key=lambda x: severity_order.get(x["severity"], 99))

    return {
        "bu_sk": bu_sk,
        "date": str(store.today.date()),
        "insights": insights,
        "total_count": len(insights),
        "critical_count": sum(1 for i in insights if i["severity"] == "critical"),
        "warning_count": sum(1 for i in insights if i["severity"] == "warning"),
        "positive_count": sum(1 for i in insights if i["severity"] in ("positive", "info")),
    }
