from __future__ import annotations

from typing import Any

from data.loader import DataStore
from data.periods import filter_period


def get_margin_analysis(store: DataStore, bu_sk: int, period: str) -> dict[str, Any]:
    """Analyze gross margin for a period."""
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)

    total_net = data["created_sales_net_amount_euro"].sum()
    total_gross = data["created_sales_gross_amount_euro"].sum()
    total_margin = total_gross - total_net
    margin_pct = (total_margin / total_gross * 100) if total_gross else 0

    return {
        "period": period,
        "total_net_euro": round(float(total_net), 2),
        "total_gross_euro": round(float(total_gross), 2),
        "total_margin_euro": round(float(total_margin), 2),
        "margin_percent": round(float(margin_pct), 1),
    }


def get_top_profitable_articles(
    store: DataStore,
    bu_sk: int,
    period: str,
    n: int = 10,
) -> dict[str, Any]:
    """Get top N articles by margin contribution."""
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)

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

    top = grouped.nlargest(n, "margin_euro")

    return {
        "period": period,
        "articles": top.to_dict("records"),
    }


def get_low_margin_alerts(store: DataStore, bu_sk: int, period: str = "30d") -> dict[str, Any]:
    """Find articles with negative or critically low margin."""
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)

    grouped = (
        data.groupby(["item_no", "series", "description"])
        .agg(
            total_qty=("created_net_quantity", "sum"),
            total_net=("created_sales_net_amount_euro", "sum"),
            total_gross=("created_sales_gross_amount_euro", "sum"),
        )
        .reset_index()
    )
    grouped["margin_euro"] = grouped["total_gross"] - grouped["total_net"]
    grouped["margin_pct"] = (grouped["margin_euro"] / grouped["total_gross"] * 100).round(1)

    # Negative margin or below 5%
    low = grouped[grouped["margin_pct"] < 5].sort_values("margin_pct")

    return {
        "period": period,
        "low_margin_articles": low.to_dict("records"),
        "count": len(low),
    }


def get_hfb_margin_analysis(store: DataStore, bu_sk: int, period: str) -> dict[str, Any]:
    """Find HFBs with strong sales but low margin (profit risk)."""
    sp = store.sales_with_products(bu_sk)
    data = filter_period(sp, "transaction_date", period, store.today)

    grouped = (
        data.groupby(["home_furnishing_business_no", "home_furnishing_business_name"])
        .agg(
            total_net=("created_sales_net_amount_euro", "sum"),
            total_gross=("created_sales_gross_amount_euro", "sum"),
        )
        .reset_index()
    )
    grouped["margin_euro"] = grouped["total_gross"] - grouped["total_net"]
    grouped["margin_pct"] = (grouped["margin_euro"] / grouped["total_gross"] * 100).round(1)
    grouped = grouped.sort_values("total_net", ascending=False)

    return {
        "period": period,
        "hfbs": grouped.to_dict("records"),
    }
