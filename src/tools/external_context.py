"""External context: holidays, promotions, and seasonal events.

Since we don't have real external APIs, this module provides a calendar of
known events that affect retail demand. In production this would pull from
IKEA's promo calendar, public holiday APIs, and weather services.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Static calendars (would be API-backed in production)
# ---------------------------------------------------------------------------

# Major holidays by country/store
HOLIDAYS: list[dict[str, Any]] = [
    {"date": "2024-01-01", "name": "New Year's Day", "region": "all", "impact": "high"},
    {"date": "2024-01-06", "name": "Epiphany", "region": "SE", "impact": "medium"},
    {"date": "2024-02-14", "name": "Valentine's Day", "region": "all", "impact": "medium"},
    {"date": "2024-03-29", "name": "Good Friday", "region": "all", "impact": "high"},
    {"date": "2024-03-31", "name": "Easter Sunday", "region": "all", "impact": "high"},
    {"date": "2024-04-01", "name": "Easter Monday", "region": "DE,NL,FR", "impact": "high"},
    {"date": "2024-05-01", "name": "Labour Day", "region": "DE,SE,FR,NL", "impact": "medium"},
    {"date": "2024-05-09", "name": "Ascension Day", "region": "DE,FR,NL,SE", "impact": "medium"},
    {"date": "2024-06-06", "name": "National Day", "region": "SE", "impact": "medium"},
    {"date": "2024-06-21", "name": "Midsummer", "region": "SE", "impact": "high"},
    {"date": "2024-09-01", "name": "Back to School", "region": "all", "impact": "high"},
    {"date": "2024-10-03", "name": "German Unity Day", "region": "DE", "impact": "medium"},
    {"date": "2024-10-31", "name": "Halloween", "region": "all", "impact": "low"},
    {"date": "2024-11-01", "name": "All Saints' Day", "region": "FR,DE", "impact": "medium"},
    {"date": "2024-11-29", "name": "Black Friday", "region": "all", "impact": "high"},
    {"date": "2024-12-02", "name": "Cyber Monday", "region": "all", "impact": "high"},
    {"date": "2024-12-24", "name": "Christmas Eve", "region": "all", "impact": "high"},
    {"date": "2024-12-25", "name": "Christmas Day", "region": "all", "impact": "high"},
    {
        "date": "2024-12-26",
        "name": "Boxing Day / 2nd Christmas",
        "region": "DE,NL,SE,UK",
        "impact": "high",
    },
    {"date": "2024-12-31", "name": "New Year's Eve", "region": "all", "impact": "medium"},
]

# IKEA promotion calendar (synthetic but realistic)
PROMOTIONS: list[dict[str, Any]] = [
    {
        "start": "2024-01-02",
        "end": "2024-01-21",
        "name": "New Year Sale",
        "category": "all",
        "discount_pct": 20,
    },
    {
        "start": "2024-02-05",
        "end": "2024-02-25",
        "name": "Bedroom Week",
        "category": "Bedroom",
        "discount_pct": 15,
    },
    {
        "start": "2024-03-04",
        "end": "2024-03-24",
        "name": "Spring Refresh",
        "category": "Living Room",
        "discount_pct": 15,
    },
    {
        "start": "2024-04-08",
        "end": "2024-04-28",
        "name": "Kitchen Event",
        "category": "Kitchen",
        "discount_pct": 20,
    },
    {
        "start": "2024-05-06",
        "end": "2024-05-26",
        "name": "Outdoor Living",
        "category": "Outdoor",
        "discount_pct": 15,
    },
    {
        "start": "2024-06-03",
        "end": "2024-06-23",
        "name": "Summer Sale",
        "category": "all",
        "discount_pct": 25,
    },
    {
        "start": "2024-07-01",
        "end": "2024-07-21",
        "name": "Storage Solutions",
        "category": "Storage",
        "discount_pct": 15,
    },
    {
        "start": "2024-08-05",
        "end": "2024-08-31",
        "name": "Back to School / Student Living",
        "category": "all",
        "discount_pct": 20,
    },
    {
        "start": "2024-09-09",
        "end": "2024-09-29",
        "name": "Cosy Autumn",
        "category": "Living Room",
        "discount_pct": 15,
    },
    {
        "start": "2024-10-07",
        "end": "2024-10-27",
        "name": "Bathroom Event",
        "category": "Bathroom",
        "discount_pct": 20,
    },
    {
        "start": "2024-11-25",
        "end": "2024-12-01",
        "name": "Black Friday Week",
        "category": "all",
        "discount_pct": 30,
    },
    {
        "start": "2024-12-02",
        "end": "2024-12-22",
        "name": "Holiday Gift Guide",
        "category": "Decoration",
        "discount_pct": 15,
    },
]

# Seasonal demand patterns (multipliers on baseline)
SEASONAL_PATTERNS: dict[int, dict[str, Any]] = {
    1: {"season": "Winter", "trend": "Post-holiday dip", "demand_factor": 0.8},
    2: {"season": "Winter", "trend": "Bedroom / bathroom refresh", "demand_factor": 0.85},
    3: {"season": "Spring", "trend": "Spring cleaning ramp-up", "demand_factor": 1.0},
    4: {"season": "Spring", "trend": "Kitchen and garden push", "demand_factor": 1.1},
    5: {"season": "Spring", "trend": "Outdoor season starts", "demand_factor": 1.15},
    6: {"season": "Summer", "trend": "Summer sale peak", "demand_factor": 1.2},
    7: {"season": "Summer", "trend": "Mid-summer dip", "demand_factor": 0.9},
    8: {"season": "Summer", "trend": "Back-to-school surge", "demand_factor": 1.2},
    9: {"season": "Autumn", "trend": "Autumn nesting", "demand_factor": 1.1},
    10: {"season": "Autumn", "trend": "Pre-holiday build", "demand_factor": 1.15},
    11: {"season": "Autumn", "trend": "Black Friday peak", "demand_factor": 1.3},
    12: {"season": "Winter", "trend": "Holiday peak", "demand_factor": 1.4},
}

# Store region mapping
STORE_REGIONS: dict[int, str] = {
    1: "DE",  # Berlin
    2: "SE",  # Stockholm
    3: "NL",  # Amsterdam
    4: "FR",  # Paris
    5: "DE",  # Munich
    6: "UK",  # London
    7: "SE",  # Malmö
    8: "DE",  # Hamburg
}


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------


def get_upcoming_events(today: pd.Timestamp, days_ahead: int = 14) -> dict[str, Any]:
    """Get holidays and events in the next N days."""
    today_date = today.date() if hasattr(today, "date") else today
    end_date = today_date + timedelta(days=days_ahead)

    upcoming_holidays = []
    for h in HOLIDAYS:
        h_date = date.fromisoformat(h["date"])
        if today_date <= h_date <= end_date:
            days_until = (h_date - today_date).days
            upcoming_holidays.append({**h, "days_until": days_until})

    return {
        "period": f"next {days_ahead} days",
        "from_date": str(today_date),
        "to_date": str(end_date),
        "events": upcoming_holidays,
        "count": len(upcoming_holidays),
    }


def get_active_promotions(today: pd.Timestamp) -> dict[str, Any]:
    """Get currently active promotions."""
    today_date = today.date() if hasattr(today, "date") else today

    active = []
    upcoming = []
    for p in PROMOTIONS:
        start = date.fromisoformat(p["start"])
        end = date.fromisoformat(p["end"])
        if start <= today_date <= end:
            days_remaining = (end - today_date).days
            active.append({**p, "days_remaining": days_remaining, "status": "active"})
        elif today_date < start and (start - today_date).days <= 14:
            days_until = (start - today_date).days
            upcoming.append({**p, "days_until": days_until, "status": "upcoming"})

    return {
        "date": str(today_date),
        "active_promotions": active,
        "upcoming_promotions": upcoming,
        "active_count": len(active),
        "upcoming_count": len(upcoming),
    }


def get_seasonal_context(today: pd.Timestamp) -> dict[str, Any]:
    """Get current seasonal context and demand pattern."""
    month = today.month
    pattern = SEASONAL_PATTERNS.get(month, {})

    return {
        "date": str(today.date() if hasattr(today, "date") else today),
        "month": month,
        "season": pattern.get("season", "Unknown"),
        "trend": pattern.get("trend", ""),
        "demand_factor": pattern.get("demand_factor", 1.0),
        "demand_label": (
            "High demand"
            if pattern.get("demand_factor", 1.0) >= 1.15
            else "Normal demand"
            if pattern.get("demand_factor", 1.0) >= 0.95
            else "Low demand period"
        ),
    }


def get_store_context(today: pd.Timestamp, bu_sk: int) -> dict[str, Any]:
    """Get combined external context for a specific store."""
    region = STORE_REGIONS.get(bu_sk, "all")
    events = get_upcoming_events(today)
    promos = get_active_promotions(today)
    seasonal = get_seasonal_context(today)

    # Filter holidays to store's region
    relevant_events = [e for e in events["events"] if e["region"] == "all" or region in e["region"]]

    return {
        "bu_sk": bu_sk,
        "region": region,
        "seasonal": seasonal,
        "upcoming_events": relevant_events,
        "event_count": len(relevant_events),
        "active_promotions": promos["active_promotions"],
        "upcoming_promotions": promos["upcoming_promotions"],
    }
