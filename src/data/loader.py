from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _parse_mixed_dates(series: pd.Series) -> pd.Series:
    """Parse dates that may be datetime strings or Excel serial numbers."""
    def _convert(val):
        if pd.isna(val):
            return pd.NaT
        s = str(val).strip()
        if "-" in s:
            return pd.to_datetime(s)
        try:
            # Excel serial number: days since 1899-12-30
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(float(s)))
        except (ValueError, OverflowError):
            return pd.NaT

    return series.apply(_convert)


def _load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


class DataStore:
    """Loads and holds all CSV data with join helpers."""

    def __init__(self, data_dir: Path | None = None) -> None:
        d = data_dir or DATA_DIR

        self.business_units = pd.read_csv(d / "Business_Unit.csv")
        self.products = pd.read_csv(d / "Product.csv")

        self.sales = pd.read_csv(d / "Sales.csv", low_memory=False)
        self.sales["transaction_date"] = pd.to_datetime(self.sales["transaction_date"])

        self.forecast = pd.read_csv(d / "Forecast.csv", low_memory=False)
        self.forecast["local_forecast_date"] = _parse_mixed_dates(
            self.forecast["local_forecast_date"]
        )

        self.stock = pd.read_csv(d / "Stock.csv", low_memory=False)
        self.stock["local_date"] = _parse_mixed_dates(self.stock["local_date"])

        # Build item_sk <-> item_no mapping for cross-table joins
        self._item_map = self.products[["item_sk", "item_no"]].drop_duplicates()

        # Determine "today" as the latest date in sales data
        self.today = self.sales["transaction_date"].max()

    # ------------------------------------------------------------------
    # Join helpers
    # ------------------------------------------------------------------

    def sales_with_products(self, bu_sk: int | None = None) -> pd.DataFrame:
        df = self.sales.merge(self.products, on="item_no", how="left")
        if bu_sk is not None:
            df = df[df["bu_sk"] == bu_sk]
        return df

    def stock_with_products(self, bu_sk: int | None = None) -> pd.DataFrame:
        df = self.stock.merge(self.products, on="item_sk", how="left")
        if bu_sk is not None:
            df = df[df["bu_sk"] == bu_sk]
        return df

    def forecast_with_products(self, bu_sk: int | None = None) -> pd.DataFrame:
        df = self.forecast.merge(self.products, on="item_sk", how="left")
        if bu_sk is not None:
            df = df[df["bu_sk"] == bu_sk]
        return df

    def sales_with_forecast(self, bu_sk: int | None = None) -> pd.DataFrame:
        """Join daily sales aggregates with forecast data."""
        # Aggregate sales to daily level per item
        sales = self.sales.copy()
        if bu_sk is not None:
            sales = sales[sales["bu_sk"] == bu_sk]
        daily_sales = (
            sales.groupby(["transaction_date", "bu_sk", "item_no"])
            .agg(
                total_qty=("created_net_quantity", "sum"),
                total_net=("created_sales_net_amount_euro", "sum"),
                total_gross=("created_sales_gross_amount_euro", "sum"),
            )
            .reset_index()
        )
        # Map item_no -> item_sk
        daily_sales = daily_sales.merge(self._item_map, on="item_no", how="left")
        # Join forecast
        merged = daily_sales.merge(
            self.forecast,
            left_on=["transaction_date", "bu_sk", "item_sk"],
            right_on=["local_forecast_date", "bu_sk", "item_sk"],
            how="left",
        )
        return merged

    def store_names(self) -> list[dict]:
        """Return list of {bu_sk, name, city} for store selector."""
        return self.business_units[["bu_sk", "bu_name", "bu_short_name", "city"]].to_dict(
            "records"
        )

    def latest_stock(self, bu_sk: int) -> pd.DataFrame:
        """Get the most recent stock snapshot for a store."""
        store_stock = self.stock[self.stock["bu_sk"] == bu_sk]
        latest_date = store_stock["local_date"].max()
        return store_stock[store_stock["local_date"] == latest_date].merge(
            self.products, on="item_sk", how="left"
        )
