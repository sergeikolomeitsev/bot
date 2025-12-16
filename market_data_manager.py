# ============================================================
# MARKET DATA MANAGER v9.6 — Real Market History
# ------------------------------------------------------------
# ✔ Хранит историю цен для каждого символа
# ✔ Отдает свежий snapshot
# ✔ Отдает history для индикаторов (EMA/RSI/GAP/VOL)
# ✔ История ограничена max_history_size
# ============================================================

import time
import logging
from typing import Dict, Any, Optional


class MarketDataManager:
    def __init__(self, config, ws_feed):
        self.logger = logging.getLogger("MarketDataManager")
        self.cfg = config
        self.ws = ws_feed

        self.symbols = config.trading.symbols

        # последние актуальные цены
        self.last_snapshot: Dict[str, float] = {}
        self.last_update_ts: Dict[str, float] = {}

        # 🔥 история цен
        self.history: Dict[str, list] = {s: [] for s in self.symbols}
        self.max_history_size = 300  # хватает для любых EMA/RSI

        # сколько времени цена считается свежей
        self.stale_seconds = 3

    # ------------------------------------------------------------
    def update(self) -> Optional[Dict[str, Any]]:
        """
        Обновляет snapshot + историю цен.
        """
        snapshot = self.ws.get_prices()

        if not snapshot:
            return None

        valid = {}

        for sym in self.symbols:
            price = snapshot.get(sym)
            if price is None:
                continue

            try:
                price = float(price)
            except:
                self.logger.error(f"Invalid price format for {sym}: {price}")
                continue

            # обновляем актуальные данные
            valid[sym] = price
            self.last_snapshot[sym] = price
            self.last_update_ts[sym] = time.time()

            # ----------------------------------------------------
            # UPDATE HISTORY
            # ----------------------------------------------------
            hist = self.history[sym]
            hist.append(price)
            if len(hist) > self.max_history_size:
                hist.pop(0)

        return valid if valid else None

    # ------------------------------------------------------------
    def get_snapshot(self) -> Dict[str, float]:
        """
        Возвращает только свежие цены (не старше stale_seconds).
        """
        now = time.time()
        fresh = {}

        for sym in self.symbols:
            ts = self.last_update_ts.get(sym)
            if not ts:
                continue

            if (now - ts) <= self.stale_seconds:
                fresh[sym] = self.last_snapshot.get(sym)

        return fresh

    # ------------------------------------------------------------
    def get_history(self, symbol: str) -> list:
        """
        Возвращает список цены для символа (до max_history_size элементов).
        """
        return self.history.get(symbol, [])
