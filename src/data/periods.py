from __future__ import annotations

from datetime import timedelta

import pandas as pd


def last_n_days(
    df: pd.DataFrame,
    date_col: str,
    n: int,
    ref_date: pd.Timestamp,
) -> pd.DataFrame:
    start = ref_date - timedelta(days=n)
    return df[(df[date_col] > start) & (df[date_col] <= ref_date)]


def last_7_days(df: pd.DataFrame, date_col: str, ref_date: pd.Timestamp) -> pd.DataFrame:
    return last_n_days(df, date_col, 7, ref_date)


def last_30_days(df: pd.DataFrame, date_col: str, ref_date: pd.Timestamp) -> pd.DataFrame:
    return last_n_days(df, date_col, 30, ref_date)


def ytd(df: pd.DataFrame, date_col: str, ref_date: pd.Timestamp) -> pd.DataFrame:
    year_start = pd.Timestamp(year=ref_date.year, month=1, day=1)
    return df[(df[date_col] >= year_start) & (df[date_col] <= ref_date)]


def previous_period(
    df: pd.DataFrame,
    date_col: str,
    n: int,
    ref_date: pd.Timestamp,
) -> pd.DataFrame:
    """Get the period *before* the last n days (for week-over-week comparisons)."""
    end = ref_date - timedelta(days=n)
    start = end - timedelta(days=n)
    return df[(df[date_col] > start) & (df[date_col] <= end)]


def filter_period(
    df: pd.DataFrame,
    date_col: str,
    period: str,
    ref_date: pd.Timestamp,
) -> pd.DataFrame:
    """Convenience dispatcher: period in {'7d', '30d', 'ytd'}."""
    if period == "7d":
        return last_7_days(df, date_col, ref_date)
    elif period == "30d":
        return last_30_days(df, date_col, ref_date)
    elif period == "ytd":
        return ytd(df, date_col, ref_date)
    else:
        raise ValueError(f"Unknown period: {period!r}. Use '7d', '30d', or 'ytd'.")
