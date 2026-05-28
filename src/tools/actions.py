from __future__ import annotations

from typing import Any

from data.loader import DataStore
from tools.sales import get_sales_vs_forecast, get_top_articles, get_declining_articles
from tools.stock import get_stock_alerts, get_availability_risks, get_oos_top_sellers
from tools.margin import get_margin_analysis


def generate_daily_priorities(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Generate ranked list of daily priorities combining sales, stock, and margin signals."""
    actions: list[dict[str, Any]] = []

    # 1. Check sales vs forecast gap
    sales_7d = get_sales_vs_forecast(store, bu_sk, "7d")
    if sales_7d["gap_percent"] < -5:
        actions.append({
            "priority": "high",
            "category": "sales",
            "action": f"Sales are {abs(sales_7d['gap_percent'])}% below forecast this week. "
            f"Gap of {abs(sales_7d['gap_units'])} units. Review floor presence of top sellers.",
            "data": sales_7d,
        })

    # 2. Check stock alerts
    stock = get_stock_alerts(store, bu_sk)
    if stock["out_of_stock_count"] > 0:
        oos_items = stock["out_of_stock"][:5]
        names = [f"{x.get('series', '')} {x.get('description', '')}" for x in oos_items]
        actions.append({
            "priority": "critical",
            "category": "availability",
            "action": f"{stock['out_of_stock_count']} articles out of stock. "
            f"Top items: {', '.join(names)}. Check replenishment and consider substitutes.",
            "data": stock,
        })

    if stock["low_stock_count"] > 0:
        actions.append({
            "priority": "high",
            "category": "availability",
            "action": f"{stock['low_stock_count']} articles below safety stock. "
            "Monitor closely and escalate supply issues.",
        })

    # 3. Check availability risks
    risks = get_availability_risks(store, bu_sk)
    critical_risks = [r for r in risks["risks"] if r["severity"] == "critical"]
    if critical_risks:
        names = [f"{r['series']} {r['description']}" for r in critical_risks[:3]]
        actions.append({
            "priority": "critical",
            "category": "availability",
            "action": f"{len(critical_risks)} articles will run out within 2 days: "
            f"{', '.join(names)}. Urgent replenishment needed.",
        })

    # 4. Check top sellers at risk
    oos_sellers = get_oos_top_sellers(store, bu_sk)
    if oos_sellers["at_risk_count"] > 0:
        actions.append({
            "priority": "high",
            "category": "sales",
            "action": f"{oos_sellers['at_risk_count']} of your top 30 sellers have stock issues. "
            "Protect availability for highest-revenue items first.",
        })

    # 5. Margin check
    margin = get_margin_analysis(store, bu_sk, "7d")
    if margin["margin_percent"] < 15:
        actions.append({
            "priority": "medium",
            "category": "margin",
            "action": f"Gross margin at {margin['margin_percent']}% this week. "
            "Review discounting activity and push higher-margin alternatives.",
        })

    # 6. Declining articles
    declining = get_declining_articles(store, bu_sk)
    if declining["articles"]:
        top_decline = declining["articles"][:3]
        names = [f"{a.get('series', '')} {a.get('description', '')}" for a in top_decline]
        actions.append({
            "priority": "medium",
            "category": "sales",
            "action": f"Declining momentum on: {', '.join(names)}. "
            "Check floor position and promotional activity.",
        })

    # 7. Always add proactive selling action
    top = get_top_articles(store, bu_sk, "7d", n=3, metric="sales")
    if top["articles"]:
        names = [f"{a.get('series', '')} {a.get('description', '')}" for a in top["articles"][:3]]
        actions.append({
            "priority": "medium",
            "category": "coaching",
            "action": f"Coach team on add-on opportunities for top sellers: {', '.join(names)}.",
        })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    actions.sort(key=lambda x: priority_order.get(x["priority"], 99))

    return {
        "store_bu_sk": bu_sk,
        "date": str(store.today.date()),
        "total_actions": len(actions),
        "actions": actions,
    }
