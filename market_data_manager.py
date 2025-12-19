# ============================================================
# MARKET DATA MANAGER v10.0 — OHLC HISTORY SUPPORT
# ------------------------------------------------------------
# Поддержка: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BNBUSDT, DOGEUSDT, AVAXUSDT
# ============================================================

import time
import logging

class MarketDataManager:
    def __init__(self, config, ws_feed):
        self.logger = logging.getLogger("MarketDataManager")
        self.cfg = config
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT", "AVAXUSDT"
        ]
        self.ws = ws_feed
        self.last_snapshot = {}
        self.last_update_ts = {}
        self.history_ohlc = {s: [] for s in self.symbols}
        self.max_history_size = 300
        self.stale_seconds = 3

    def update(self):
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
            except Exception:
                self.logger.error(f"Invalid price format for {sym}: {price}")
                continue
            valid[sym] = price
            self.last_snapshot[sym] = price
            self.last_update_ts[sym] = time.time()
            # - заполнение новой ohlc-истории
            history_ohlc = self.ws.get_ohlc_history(sym, self.max_history_size)
            if history_ohlc:
                self.history_ohlc[sym] = history_ohlc
        return valid if valid else None

    def get_snapshot(self):
        now = time.time()
        fresh = {}
        for sym in self.symbols:
            ts = self.last_update_ts.get(sym)
            if not ts:
                continue
            if (now - ts) <= self.stale_seconds:
                fresh[sym] = self.last_snapshot.get(sym)
        return fresh

    def get_history(self, symbol: str) -> list:
        return self.history_ohlc.get(symbol, [])