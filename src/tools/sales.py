from __future__ import annotations

from typing import Any

from data.loader import DataStore
from data.periods import filter_period, previous_period


def get_sales_vs_forecast(store: DataStore, bu_sk: int, period: str) -> dict[str, Any]:
    """Compare actual sales to forecast for a given period."""
    sf = store.sales_with_forecast(bu_sk)
    data = filter_period(sf, "transaction_date", period, store.today)

    actual_units = data["total_qty"].sum()
    actual_net = data["total_net"].sum()
    forecast_units = data["operational_forecast_units"].sum()

    gap_units = actual_units - forecast_units
    gap_pct = (gap_units / forecast_units * 100) if forecast_units else 0

    return {
        "period": period,
        "actual_sales_units": int(actual_units),
        "actual_sales_net_euro": round(float(actual_net), 2),
        "forecast_units": round(float(forecast_units), 2),
        "gap_units": round(float(gap_units), 2),
        "gap_percent": round(float(gap_pct), 1),
        "status": "above" if gap_units >= 0 else "below",
    }


def get_sales_summary(store: DataStore, bu_sk: int) -> dict[str, Any]:
    """Get sales vs forecast for all three time periods."""
    return {
        "7d": get_sales_vs_forecast(store, bu_sk, "7d"),
        "30d": get_sales_vs_forecast(store, bu_sk, "30d"),
        "ytd": get_sales_vs_forecast(store, bu_sk, "ytd"),
    }


def get_top_articles(
    store: DataStore,
    bu_sk: int,
    period: str,
    n: int = 10,
    metric: str = "sales",
) -> dict[str, Any]:
    """Get top N articles by sales volume or profit."""
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)

    if metric == "sales":
        sort_col = "total_net"
    else:
        sort_col = "total_net"  # will be overridden below for profit

    grouped = (
        data.groupby(["item_no", "series", "description", "colour"])
        .agg(
            total_qty=("created_net_quantity", "sum"),
            total_net=("created_sales_net_amount_euro", "sum"),
            total_gross=("created_sales_gross_amount_euro", "sum"),
        )
        .reset_index()
    )
    grouped["margin_euro"] = grouped["total_gross"] - grouped["total_net"]
    grouped["margin_pct"] = (grouped["margin_euro"] / grouped["total_gross"] * 100).round(1)

    if metric == "profit":
        sort_col = "margin_euro"

    top = grouped.nlargest(n, sort_col)

    return {
        "period": period,
        "metric": metric,
        "articles": top.to_dict("records"),
    }


def get_hfb_performance(store: DataStore, bu_sk: int, period: str) -> dict[str, Any]:
    """Get Home Furnishing Business performance for a period."""
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)

    grouped = (
        data.groupby(["home_furnishing_business_no", "home_furnishing_business_name"])
        .agg(
            total_qty=("created_net_quantity", "sum"),
            total_net=("created_sales_net_amount_euro", "sum"),
            total_gross=("created_sales_gross_amount_euro", "sum"),
        )
        .reset_index()
    )
    grouped["margin_euro"] = grouped["total_gross"] - grouped["total_net"]
    grouped["margin_pct"] = (grouped["margin_euro"] / grouped["total_gross"] * 100).round(1)
    grouped = grouped.sort_values("total_net", ascending=False)

    # Week-over-week growth for each HFB
    if period in ("7d", "30d"):
        days = 7 if period == "7d" else 30
        prev = previous_period(sp, "transaction_date", days, store.today)
        prev_grouped = (
            prev.groupby(["home_furnishing_business_no"])
            .agg(prev_net=("created_sales_net_amount_euro", "sum"))
            .reset_index()
        )
        grouped = grouped.merge(prev_grouped, on="home_furnishing_business_no", how="left")
        grouped["prev_net"] = grouped["prev_net"].fillna(0)
        grouped["growth_pct"] = (
            (grouped["total_net"] - grouped["prev_net"]) / grouped["prev_net"] * 100
        ).round(1)
        grouped["growth_pct"] = (
            grouped["growth_pct"].replace([float("inf"), float("-inf")], 0).fillna(0)
        )

    return {
        "period": period,
        "hfbs": grouped.to_dict("records"),
    }


def get_declining_articles(store: DataStore, bu_sk: int, n: int = 10) -> dict[str, Any]:
    """Find articles with declining sales momentum over last 30 days."""
    sp = store.sales_with_products(bu_sk)

    # Compare last 7 days vs the 7 days before that
    recent = filter_period(sp, "transaction_date", "7d", store.today)
    prior = previous_period(sp, "transaction_date", 7, store.today)

    recent_g = (
        recent.groupby(["item_no", "series", "description"])
        .agg(recent_net=("created_sales_net_amount_euro", "sum"))
        .reset_index()
    )
    prior_g = (
        prior.groupby(["item_no", "series", "description"])
        .agg(prior_net=("created_sales_net_amount_euro", "sum"))
        .reset_index()
    )

    merged = recent_g.merge(prior_g, on=["item_no", "series", "description"], how="outer").fillna(0)
    merged["change_pct"] = (
        (merged["recent_net"] - merged["prior_net"]) / merged["prior_net"] * 100
    ).round(1)
    merged["change_pct"] = merged["change_pct"].replace([float("inf"), float("-inf")], 0).fillna(0)

    declining = merged[merged["change_pct"] < 0].nsmallest(n, "change_pct")

    return {
        "articles": declining.to_dict("records"),
    }
