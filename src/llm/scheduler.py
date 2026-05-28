"""Alert scheduler — generates proactive insights on a schedule.

In production this would be a background worker (Celery, APScheduler, or cron).
For the hackathon demo, we use FastAPI's lifespan events and an in-memory cache
that refreshes periodically.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from datetime import datetime

from data.loader import DataStore
from tools.insights import generate_proactive_insights

logger = logging.getLogger(__name__)


class AlertScheduler:
    """Generates and caches proactive insights per store.

    Insights are pre-computed at startup and refreshed every N minutes.
    This simulates a real scheduler that would trigger before store opening hours.
    """

    def __init__(self, store: DataStore, refresh_interval_minutes: int = 30) -> None:
        self.store = store
        self.refresh_interval = refresh_interval_minutes * 60  # seconds
        self._cache: dict[int, dict[str, Any]] = {}
        self._last_refresh: dict[int, str] = {}
        self._task: asyncio.Task | None = None

    def get_insights(self, bu_sk: int) -> dict[str, Any]:
        """Get cached insights for a store. Generates on first call if not cached."""
        if bu_sk not in self._cache:
            self._refresh_store(bu_sk)
        result = self._cache.get(bu_sk, {"insights": [], "total_count": 0})
        result["cached_at"] = self._last_refresh.get(bu_sk, "never")
        return result

    def _refresh_store(self, bu_sk: int) -> None:
        """Refresh insights for a single store."""
        try:
            insights = generate_proactive_insights(self.store, bu_sk)
            self._cache[bu_sk] = insights
            self._last_refresh[bu_sk] = datetime.now().isoformat()
            logger.info(
                f"Refreshed insights for store {bu_sk}: "
                f"{insights['total_count']} insights "
                f"({insights['critical_count']} critical)"
            )
        except Exception as e:
            logger.error(f"Failed to refresh insights for store {bu_sk}: {e}")

    def refresh_all(self) -> None:
        """Refresh insights for all stores."""
        store_list = self.store.store_names()
        for s in store_list:
            self._refresh_store(s["bu_sk"])
        logger.info(f"Refreshed insights for {len(store_list)} stores")

    async def start(self) -> None:
        """Start the background refresh loop."""
        # Initial refresh for all stores
        self.refresh_all()

        # Schedule periodic refresh
        async def _loop():
            while True:
                await asyncio.sleep(self.refresh_interval)
                self.refresh_all()

        self._task = asyncio.create_task(_loop())
        logger.info(
            f"Alert scheduler started (refresh every {self.refresh_interval // 60} min)"
        )

    async def stop(self) -> None:
        """Stop the background refresh loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Alert scheduler stopped")
