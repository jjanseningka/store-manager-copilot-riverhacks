from __future__ import annotations

from typing import Any

from data.loader import DataStore
from data.periods import filter_period


def get_stock_alerts(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Get current stock alerts — items below safety stock or out of stock."""
    latest = store.latest_stock(bu_sk)

    # Out of stock: available_stock <= 0
    oos = latest[latest["available_stock"] <= 0]
    # Low stock: available_stock > 0 but below demand_stock
    low = latest[(latest["available_stock"] > 0) & (latest["available_stock"] < latest["demand_stock"])]
    # Healthy
    healthy = latest[latest["available_stock"] >= latest["demand_stock"]]

    cols = ["item_sk", "item_no", "series", "description", "available_stock", "demand_stock"]
    available_cols = [c for c in cols if c in latest.columns]

    return {
        "total_items": len(latest),
        "out_of_stock_count": len(oos),
        "low_stock_count": len(low),
        "healthy_count": len(healthy),
        "out_of_stock": oos[available_cols].head(20).to_dict("records"),
        "low_stock": low[available_cols].head(20).to_dict("records"),
    }


def get_availability_risks(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Identify articles at risk of going out of stock based on stock trends."""
    stock_data = store.stock_with_products(bu_sk)
    today = store.today

    # Look at last 7 days of stock movement
    recent = filter_period(stock_data, "local_date", "7d", today)

    if recent.empty:
        return {"risks": [], "message": "No recent stock data available."}

    # Group by item_sk and check trend
    risks = []
    for item_sk, group in recent.groupby("item_sk"):
        group = group.sort_values("local_date")
        if len(group) < 2:
            continue

        first_stock = group.iloc[0]["available_stock"]
        last_stock = group.iloc[-1]["available_stock"]
        daily_burn = (first_stock - last_stock) / len(group)

        if daily_burn > 0 and last_stock > 0:
            days_until_oos = last_stock / daily_burn
            if days_until_oos <= 7:  # At risk within a week
                row = group.iloc[-1]
                risks.append({
                    "item_sk": int(item_sk),
                    "series": row.get("series", ""),
                    "description": row.get("description", ""),
                    "current_stock": int(last_stock),
                    "daily_burn_rate": round(float(daily_burn), 1),
                    "days_until_oos": round(float(days_until_oos), 1),
                    "severity": "critical" if days_until_oos <= 2 else "warning",
                })

    risks.sort(key=lambda x: x["days_until_oos"])
    return {"risks": risks[:15]}


def get_oos_top_sellers(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Find top-selling articles that are currently out of stock or low stock."""
    # Get top sellers by volume
    sp = store.sales_with_products(bu_sk)
    recent_sales = filter_period(sp, "transaction_date", "30d", store.today)

    top_sellers = (
        recent_sales.groupby(["item_no", "series", "description"])
        .agg(total_qty=("created_net_quantity", "sum"), total_net=("created_sales_net_amount_euro", "sum"))
        .reset_index()
        .nlargest(30, "total_net")
    )

    # Check current stock for these items
    latest = store.latest_stock(bu_sk)
    # latest_stock already has product info via item_sk merge, including item_no

    merged = top_sellers.merge(
        latest[["item_no", "available_stock", "demand_stock"]].dropna(subset=["item_no"]),
        on="item_no",
        how="left",
    )

    at_risk = merged[merged["available_stock"] < merged["demand_stock"]].sort_values(
        "total_net", ascending=False
    )

    return {
        "top_sellers_at_risk": at_risk.to_dict("records"),
        "total_top_sellers_checked": len(top_sellers),
        "at_risk_count": len(at_risk),
    }


def get_overstock_articles(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Find articles overstocked relative to forecast."""
    latest = store.latest_stock(bu_sk)
    overstocked = latest[latest["avoidable_stock"] > latest["acceptable_stock"]].copy()

    if overstocked.empty:
        return {"overstocked": [], "count": 0}

    overstocked = overstocked.sort_values("avoidable_stock", ascending=False)
    cols = ["item_sk", "series", "description", "available_stock", "acceptable_stock", "avoidable_stock"]
    available_cols = [c for c in cols if c in overstocked.columns]

    return {
        "overstocked": overstocked[available_cols].head(15).to_dict("records"),
        "count": len(overstocked),
    }
