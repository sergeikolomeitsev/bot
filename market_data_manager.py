# ============================================================
# MARKET DATA MANAGER v10.2 — OHLC HISTORY + STABLE WS APPEND
# ------------------------------------------------------------
# Поддержка: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BNBUSDT, DOGEUSDT, AVAXUSDT
# При старте сразу загружает историю через REST Bybit,
# Live-бары из WebSocket аккуратно ДОПИСЫВАЮТСЯ (не затирают всю историю!)
# ============================================================

import time
import logging
import requests

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

        # --- BACKFILL OHLC history via Bybit REST API on startup ---
        self.backfill_history_via_rest()

        # Для совместимости с legacy heartbeat:
        self.history = self.history_ohlc

    def backfill_history_via_rest(self):
        """Загрузка истории OHLC через публичный REST Bybit сразу при инициализации"""
        def fetch_bybit_history(symbol, interval="1", limit=300):
            url = f"https://api.bybit.com/v5/market/kline"
            params = dict(category="linear", symbol=symbol, interval=interval, limit=limit)
            try:
                resp = requests.get(url, params=params, timeout=10)
                result = resp.json()
                bars = result.get("result", {}).get("list", [])
                bars_sorted = sorted(bars, key=lambda x: int(x[0]))
                ohlcs = []
                for bar in bars_sorted:
                    ohlcs.append({
                        "start": int(bar[0]),
                        "open": float(bar[1]),
                        "high": float(bar[2]),
                        "low": float(bar[3]),
                        "close": float(bar[4]),
                        "volume": float(bar[5]),
                        "end": int(bar[8]) if len(bar) > 8 else None,
                    })
                return ohlcs
            except Exception as e:
                self.logger.error(f"Failed to fetch backfill for {symbol}: {e}")
                return []
        for sym in self.symbols:
            ohlc = fetch_bybit_history(sym, interval="1", limit=self.max_history_size)
            if ohlc:
                self.history_ohlc[sym] = ohlc

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
            # --- APPEND ONLY: добавляем live-бары WebSocket (НЕ перезаписываем всю историю!)
            ws_bars = self.ws.get_ohlc_history(sym, self.max_history_size)
            if ws_bars:
                # определяем уже имеющиеся start'ы, чтобы не было дубликатов
                existing_starts = set(bar['start'] for bar in self.history_ohlc[sym])
                for bar in ws_bars:
                    if bar['start'] not in existing_starts:
                        self.history_ohlc[sym].append(bar)
                # Ограничиваем длину истории
                if len(self.history_ohlc[sym]) > self.max_history_size:
                    self.history_ohlc[sym] = self.history_ohlc[sym][-self.max_history_size:]
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