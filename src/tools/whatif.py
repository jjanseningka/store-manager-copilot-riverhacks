"""What-if analysis sparring tool.

Lets store managers explore scenarios like:
- What if we increase/decrease price by X%?
- What if we improve availability to 100%?
- What if demand increases by X% (e.g., due to promotion)?
"""

from __future__ import annotations

from typing import Any

from data.loader import DataStore
from data.periods import filter_period


def whatif_price_change(
    store: DataStore, bu_sk: int, item_no: int, price_change_pct: float, period: str = "30d"
) -> dict[str, Any]:
    """Simulate impact of a price change on margin and estimated volume.

    Uses price elasticity heuristic: 1% price increase → ~1.5% volume decrease
    (typical IKEA home furnishing elasticity).
    """
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)
    item_data = data[data["item_no"] == item_no]

    if item_data.empty:
        return {"error": f"No sales data found for item {item_no} in period {period}"}

    current_qty = int(item_data["created_net_quantity"].sum())
    current_net = float(item_data["created_sales_net_amount_euro"].sum())
    current_gross = float(item_data["created_sales_gross_amount_euro"].sum())
    current_margin = current_gross - current_net

    article_info = item_data.iloc[0]
    series = article_info.get("series", "")
    description = article_info.get("description", "")

    # Price elasticity model (simplified)
    elasticity = -1.5  # 1% price increase → 1.5% volume drop
    volume_change_pct = price_change_pct * elasticity
    new_qty = max(0, current_qty * (1 + volume_change_pct / 100))

    # New revenue: only the selling price (gross) changes. Cost (net) stays the same.
    # In retail: net = cost to IKEA, gross = selling price to customer
    # Margin = gross - net = what IKEA keeps
    avg_cost_net = current_net / current_qty if current_qty else 0
    avg_price_gross = current_gross / current_qty if current_qty else 0
    new_price_gross = avg_price_gross * (1 + price_change_pct / 100)

    # Cost per unit doesn't change with price — only volume changes
    new_net = new_qty * avg_cost_net
    new_gross = new_qty * new_price_gross
    new_margin = new_gross - new_net

    return {
        "scenario": f"Price {'increase' if price_change_pct > 0 else 'decrease'} of {price_change_pct}%",
        "article": f"{series} {description}",
        "item_no": item_no,
        "period": period,
        "current": {
            "qty": current_qty,
            "net_euro": round(current_net, 2),
            "gross_euro": round(current_gross, 2),
            "margin_euro": round(current_margin, 2),
            "avg_price_euro": round(avg_price_gross, 2),
        },
        "projected": {
            "qty": round(new_qty),
            "net_euro": round(new_net, 2),
            "gross_euro": round(new_gross, 2),
            "margin_euro": round(new_margin, 2),
            "avg_price_euro": round(new_price_gross, 2),
            "volume_change_pct": round(volume_change_pct, 1),
        },
        "delta": {
            "qty_change": round(new_qty - current_qty),
            "revenue_change_euro": round(new_gross - current_gross, 2),
            "margin_change_euro": round(new_margin - current_margin, 2),
        },
        "note": "Based on estimated price elasticity of -1.5. Actual results may vary.",
    }


def whatif_availability_improvement(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Estimate revenue uplift if all OOS items were brought back in stock.

    Uses average daily sales rate of each OOS item to project gains.
    """
    from tools.stock import get_stock_alerts

    alerts = get_stock_alerts(store, bu_sk)
    oos_items = alerts.get("out_of_stock", [])
    if not oos_items:
        return {
            "scenario": "Availability improvement to 100%",
            "message": "No items are currently out of stock — great job!",
            "estimated_daily_uplift_euro": 0,
            "estimated_weekly_uplift_euro": 0,
        }

    sp = store.sales_with_products(bu_sk)

    total_daily_uplift = 0
    items_detail = []

    for item in oos_items:
        item_no = item.get("item_no")
        if item_no is None:
            continue
        # Look at average daily sales over 30d period before they went OOS
        item_sales = sp[sp["item_no"] == item_no]
        if item_sales.empty:
            continue

        total_net = float(item_sales["created_sales_net_amount_euro"].sum())
        date_range = (
            item_sales["transaction_date"].max() - item_sales["transaction_date"].min()
        ).days
        daily_rate = total_net / max(date_range, 1)

        total_daily_uplift += daily_rate
        items_detail.append(
            {
                "article": f"{item.get('series', '')} {item.get('description', '')}",
                "item_no": item_no,
                "est_daily_revenue_euro": round(daily_rate, 2),
            }
        )

    items_detail.sort(key=lambda x: x["est_daily_revenue_euro"], reverse=True)

    return {
        "scenario": "Bring all OOS items back in stock",
        "oos_item_count": len(oos_items),
        "estimated_daily_uplift_euro": round(total_daily_uplift, 2),
        "estimated_weekly_uplift_euro": round(total_daily_uplift * 7, 2),
        "estimated_monthly_uplift_euro": round(total_daily_uplift * 30, 2),
        "top_items": items_detail[:10],
        "note": "Based on historical average daily revenue per item.",
    }


def whatif_demand_surge(
    store: DataStore, bu_sk: int, demand_increase_pct: float, period: str = "7d"
) -> dict[str, Any]:
    """Simulate impact of a demand increase (e.g., from a promotion or event).

    Checks which items would run out of stock under increased demand.
    """
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)

    latest_stock = store.latest_stock(bu_sk)

    # Get daily sell-through per item
    days_in_period = {"7d": 7, "30d": 30, "ytd": 365}.get(period, 7)
    item_sales = (
        data.groupby(["item_no", "series", "description"])
        .agg(total_qty=("created_net_quantity", "sum"))
        .reset_index()
    )
    item_sales["daily_rate"] = item_sales["total_qty"] / days_in_period
    item_sales["surge_daily_rate"] = item_sales["daily_rate"] * (1 + demand_increase_pct / 100)

    # Check stock coverage
    stock_lookup = latest_stock.set_index("item_no")["available_stock"].to_dict()

    at_risk = []
    for _, row in item_sales.iterrows():
        stock = stock_lookup.get(row["item_no"], 0)
        days_cover_normal = stock / row["daily_rate"] if row["daily_rate"] > 0 else 999
        days_cover_surge = stock / row["surge_daily_rate"] if row["surge_daily_rate"] > 0 else 999

        if days_cover_surge < 7:
            at_risk.append(
                {
                    "article": f"{row['series']} {row['description']}",
                    "item_no": int(row["item_no"]),
                    "current_stock": int(stock),
                    "normal_daily_rate": round(row["daily_rate"], 1),
                    "surge_daily_rate": round(row["surge_daily_rate"], 1),
                    "days_cover_normal": round(days_cover_normal, 1),
                    "days_cover_surge": round(days_cover_surge, 1),
                }
            )

    at_risk.sort(key=lambda x: x["days_cover_surge"])

    return {
        "scenario": f"Demand increase of {demand_increase_pct}%",
        "period_basis": period,
        "items_at_risk": at_risk,
        "at_risk_count": len(at_risk),
        "total_items_analysed": len(item_sales),
        "note": f"Items that would run out within 7 days under {demand_increase_pct}% demand increase.",
    }
