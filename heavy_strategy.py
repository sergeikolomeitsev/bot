# ============================================================
# HEAVY STRATEGY v11.0 — TP/SL, trailing, ADX+ATR, risk/MM, комиссия
# ============================================================

from typing import Dict, Any, List, Optional

class HeavyStrategy:
    INIT_STACK = 300.0
    TAKE_PROFIT_PCT = 0.004
    STOP_LOSS_PCT = 0.002
    TRAILING_PCT = 0.002
    FEE_PCT = 0.0007
    SPREAD_PCT = 0.0005
    MAX_RISK_PCT = 0.05
    MIN_RISK_PCT = 0.01
    MIN_ADX = 10
    MIN_ATR_RATIO = 0.0001
    MIN_CONFIDENCE = 0.04

    def __init__(self, portfolio, analyzer=None):
        self.portfolio = portfolio
        self.analyzer = analyzer
        self.active_trades = {}
        self.balance = self.INIT_STACK
        self.in_market = set()
        self.last_signals = {}

    @property
    def positions(self):
        return self.portfolio.positions

    @property
    def trades(self):
        return self.portfolio.trades

    def update_balance(self):
        self.balance = self.INIT_STACK + sum([t.get("pnl",0) for t in self.portfolio.trades])

    def can_trade(self):
        self.update_balance()
        return self.balance >= self.INIT_STACK

    def get_trade_amount(self, price, confidence):
        stack = max(self.balance, self.INIT_STACK)
        pct = max(self.MIN_RISK_PCT, min(confidence, self.MAX_RISK_PCT))
        usdt = stack * pct
        return max(round(usdt/price, 6), 0.0001)

    def open_position(self, symbol, price, confidence, side):
        if not self.can_trade(): return
        if symbol in self.active_trades: return
        amount = self.get_trade_amount(price, confidence)
        fee = self.FEE_PCT + self.SPREAD_PCT
        tp  = price * (1 + self.TAKE_PROFIT_PCT - fee) if side=="long" else price * (1 - self.TAKE_PROFIT_PCT + fee)
        sl  = price * (1 - self.STOP_LOSS_PCT - fee) if side=="long" else price * (1 + self.STOP_LOSS_PCT + fee)
        trailing = self.TRAILING_PCT * price
        self.portfolio.open_position(symbol, price, amount, side)
        self.active_trades[symbol] = {"entry": price, "amount": amount, "side": side, "tp": tp, "sl": sl, "trailing": trailing, "extremum": price}

    def close_position(self, symbol, price):
        self.portfolio.close_position(symbol, price)
        self.active_trades.pop(symbol, None)
        self.in_market.discard(symbol)
        self.update_balance()

    def on_tick(self, snapshot):
        for symbol, trade in list(self.active_trades.items()):
            price = snapshot.get(symbol)
            if not price: continue
            # trailing update
            if trade["side"] == "long":
                if price > trade["extremum"]: trade["extremum"] = price
                stop = trade["extremum"] - trade["trailing"]
                if price <= stop or price >= trade["tp"] or price <= trade["sl"]:
                    self.close_position(symbol, price)
            else:
                if price < trade["extremum"]: trade["extremum"] = price
                stop = trade["extremum"] + trade["trailing"]
                if price >= stop or price <= trade["tp"] or price >= trade["sl"]:
                    self.close_position(symbol, price)

    def generate_signal(self, snapshot, symbol, history=None):
        print(f"[RISKY DEBUG] {symbol}: generate_signal called, len(history)={len(history) if history else None}")

        if symbol in self.active_trades:
            print(f"[RISKY DEBUG] {symbol}: already in active_trades, skipping.")
            return None
        if not history:
            print(f"[RISKY DEBUG] {symbol}: history is None or empty!")
            return None
        if len(history) < 30:
            print(f"[RISKY DEBUG] {symbol}: insufficient history ({len(history)} bars).")
            return None
        if not self.analyzer:
            print(f"[RISKY DEBUG] {symbol}: analyzer is None!")
            return None

        highs = [bar['high'] for bar in history]
        lows = [bar['low'] for bar in history]
        closes = [bar['close'] for bar in history]
        price = closes[-1]

        ema_fast = self.analyzer.ema(closes, 7)
        ema_slow = self.analyzer.ema(closes, 25)
        adx_val = self.analyzer.adx(highs, lows, closes, 14)
        atr_val = self.analyzer.atr(highs, lows, closes, 14)
        rsi_val = self.analyzer.rsi(closes, 14)

        print(
            f"[RISKY DEBUG] {symbol}: price={price}, ema_fast={ema_fast}, ema_slow={ema_slow}, adx={adx_val}, atr={atr_val}, rsi={rsi_val}"
        )

        if None in (ema_fast, ema_slow, adx_val, atr_val, rsi_val):
            print(f"[RISKY DEBUG] {symbol}: missing indicator(s), skip.")
            return None

        # Фильтр ADX и ATR — остался для защиты от совсем плоских рынков (можете убрать MIN_ATR_RATIO ещё ниже для ultra risk)
        if adx_val < self.MIN_ADX or atr_val / price < self.MIN_ATR_RATIO:
            print(f"[RISKY DEBUG] {symbol}: filtered by ADX/ATR (adx={adx_val}, atr/price={atr_val / price:.5f})")
            return {"symbol": symbol, "signal": "hold", "strength": 0.0}

        # Confidence без GAP — только риск от ADX, можно усилить
        confidence = min((adx_val - self.MIN_ADX) * 0.07 + 0.03, self.MAX_RISK_PCT)
        print(f"[RISKY DEBUG] {symbol}: confidence={confidence}, min_required={self.MIN_CONFIDENCE}")

        # Сверх рисковые условия — только кросс EMA и мягкий фильтр RSI
        signal = "hold"
        if ema_fast > ema_slow and rsi_val < 70 and confidence >= self.MIN_CONFIDENCE:
            print(f"[RISKY DEBUG] {symbol}: LONG TRIGGERED")
            signal = "long"
        elif ema_fast < ema_slow and rsi_val > 30 and confidence >= self.MIN_CONFIDENCE:
            print(f"[RISKY DEBUG] {symbol}: SHORT TRIGGERED")
            signal = "short"
        else:
            print(f"[RISKY DEBUG] {symbol}: No entry conditions met (signal=hold).")

        return {"symbol": symbol, "signal": signal, "strength": confidence}

    def get_pnl(self, snapshot=None):
        realized = sum([t.get('pnl', 0) for t in self.trades])
        unrealized = 0
        if snapshot:
            for sym, pos in self.positions.items():
                price = snapshot.get(sym)
                if price is not None:
                    entry = pos["entry_price"]
                    size = pos["amount"]
                    side = pos.get("side", "long")
                    if side == "long":
                        unrealized += (price - entry) * size
                    else:
                        unrealized += (entry - price) * size
        return {'realized': realized, 'unrealized': unrealized}