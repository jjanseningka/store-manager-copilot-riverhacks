from __future__ import annotations

from data.loader import DataStore


def validate_article_references(response: str, store: DataStore) -> list[str]:
    """Check that article names mentioned in the response actually exist in the data."""
    warnings = []
    known_series = set(store.products["series"].dropna().str.upper().unique())

    # Extract potential series names (all-caps words that could be IKEA series)
    import re

    # IKEA series names are typically ALL CAPS, 3+ letters
    potential_refs = set(re.findall(r"\b([A-Z]{3,})\b", response))

    # Filter to words that look like series names (exclude common words)
    common_words = {
        "THE",
        "AND",
        "FOR",
        "ARE",
        "NOT",
        "BUT",
        "HAS",
        "HAD",
        "WAS",
        "HFB",
        "OOS",
        "OSA",
        "YTD",
        "KEY",
        "TOP",
        "ALL",
        "LOW",
        "HIGH",
        "NET",
        "GOOD",
        "ACTION",
        "SALES",
        "STOCK",
        "MARGIN",
        "TOTAL",
        "STORE",
        "WEEK",
        "DAYS",
        "TODAY",
        "ITEMS",
        "UNITS",
        "EURO",
        "CRITICAL",
        "WARNING",
        "STATUS",
        "PRIORITY",
        "FOCUS",
        "TEAM",
        "COACH",
        "BRIEF",
        "HUDDLE",
        "MORNING",
        "PRODUCT",
        "ARTICLE",
        "AVAILABLE",
        "DEMAND",
    }
    potential_refs -= common_words

    for ref in potential_refs:
        if ref not in known_series:
            warnings.append(
                f"⚠️ Series name '{ref}' mentioned in response but not found in product data."
            )

    return warnings


def validate_numbers_reasonable(response: str) -> list[str]:
    """Basic sanity check on numbers in the response."""
    warnings = []
    import re

    # Check for suspiciously large euro amounts (> 10M in a single article context)
    euro_amounts = re.findall(r"€\s?([\d,]+(?:\.\d+)?)", response)
    for amount_str in euro_amounts:
        try:
            amount = float(amount_str.replace(",", ""))
            if amount > 10_000_000:
                warnings.append(f"⚠️ Unusually large amount €{amount_str} — verify this is correct.")
        except ValueError:
            pass

    return warnings
