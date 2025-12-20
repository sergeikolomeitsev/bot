# ============================================================
# HEAVY STRATEGY v11.3 — TP/SL, trailing, ADX+ATR, risk/MM, комиссия,
# индивидуальный JSON-логгер (стратегии) + ДЕБАГ-ЛОГГЕР портфельных операций
# ============================================================

from typing import Dict, Any, List, Optional
from debug_logger import DebugLogger

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
    MIN_ATR_RATIO = 0.00005
    MIN_CONFIDENCE = 0.04

    def __init__(self, portfolio, analyzer=None):
        self.logger = DebugLogger("heavy_strategy_debug.json", max_records=10000)
        self.logger.enable()
        self.portfolio_logger = DebugLogger("heavy_portfolio_debug.json", max_records=10000)
        self.portfolio_logger.enable()
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
        if not self.can_trade():
            self.portfolio_logger.log("open_position_blocked", symbol=symbol, reason="cant_trade", balance=self.balance)
            return
        if symbol in self.active_trades:
            self.portfolio_logger.log("open_position_blocked", symbol=symbol, reason="already_active", active_trades=list(self.active_trades.keys()))
            return
        amount = self.get_trade_amount(price, confidence)
        fee = self.FEE_PCT + self.SPREAD_PCT
        tp  = price * (1 + self.TAKE_PROFIT_PCT - fee) if side=="long" else price * (1 - self.TAKE_PROFIT_PCT + fee)
        sl  = price * (1 - self.STOP_LOSS_PCT - fee) if side=="long" else price * (1 + self.STOP_LOSS_PCT + fee)
        trailing = self.TRAILING_PCT * price
        self.portfolio.open_position(symbol, price, amount, side)
        self.active_trades[symbol] = {"entry": price, "amount": amount, "side": side, "tp": tp, "sl": sl, "trailing": trailing, "extremum": price}
        self.portfolio_logger.log(
            "open_position_success",
            symbol=symbol, price=price, amount=amount, side=side,
            confidence=confidence, tp=tp, sl=sl, trailing=trailing
        )

    def close_position(self, symbol, price):
        if symbol not in self.active_trades:
            self.portfolio_logger.log("close_position_blocked", symbol=symbol, reason="not_active")
        self.portfolio.close_position(symbol, price)
        self.active_trades.pop(symbol, None)
        self.in_market.discard(symbol)
        self.update_balance()
        self.portfolio_logger.log("close_position_success", symbol=symbol, price=price)

    def on_tick(self, snapshot):
        for symbol, trade in list(self.active_trades.items()):
            price = snapshot.get(symbol)
            if not price:
                continue
            if trade["side"] == "long":
                if price > trade["extremum"]:
                    trade["extremum"] = price
                stop = trade["extremum"] - trade["trailing"]
                if price <= stop or price >= trade["tp"] or price <= trade["sl"]:
                    self.close_position(symbol, price)
            else:
                if price < trade["extremum"]:
                    trade["extremum"] = price
                stop = trade["extremum"] + trade["trailing"]
                if price >= stop or price <= trade["tp"] or price >= trade["sl"]:
                    self.close_position(symbol, price)

    def generate_signal(self, snapshot, symbol, history=None):
        self.logger.log("generate_signal called", symbol=symbol, len_history=len(history) if history else None)
        if symbol in self.active_trades:
            self.logger.log("already in active_trades", symbol=symbol)
            return None
        if not history:
            self.logger.log("history is None or empty", symbol=symbol)
            return None
        if len(history) < 30:
            self.logger.log("insufficient history", symbol=symbol, length=len(history))
            return None
        if not self.analyzer:
            self.logger.log("analyzer is None", symbol=symbol)
            return None

        highs  = [bar['high'] for bar in history]
        lows   = [bar['low']  for bar in history]
        closes = [bar['close'] for bar in history]
        price = closes[-1]

        ema_fast = self.analyzer.ema(closes, 7)
        ema_slow = self.analyzer.ema(closes, 25)
        adx_val  = self.analyzer.adx(highs, lows, closes, 14)
        atr_val  = self.analyzer.atr(highs, lows, closes, 14)
        rsi_val  = self.analyzer.rsi(closes, 14)

        self.logger.log(
            "indicators",
            symbol=symbol,
            price=price,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            adx=adx_val,
            atr=atr_val,
            rsi=rsi_val
        )

        if None in (ema_fast, ema_slow, adx_val, atr_val, rsi_val):
            self.logger.log("missing indicator", symbol=symbol)
            return None

        if adx_val < self.MIN_ADX or atr_val / price < self.MIN_ATR_RATIO:
            self.logger.log("filtered by ADX/ATR", symbol=symbol, adx=adx_val, atr=atr_val, price=price)
            return {"symbol": symbol, "signal": "hold", "strength": 0.0}

        confidence = min((adx_val - self.MIN_ADX) * 0.07 + 0.03, self.MAX_RISK_PCT)
        self.logger.log("confidence calc", symbol=symbol, confidence=confidence, min_required=self.MIN_CONFIDENCE)

        signal = "hold"
        if ema_fast > ema_slow and confidence >= self.MIN_CONFIDENCE:
            self.logger.log("LONG TRIGGERED", symbol=symbol, price=price, ema_fast=ema_fast, ema_slow=ema_slow, confidence=confidence)
            signal = "long"
        elif ema_fast < ema_slow and confidence >= self.MIN_CONFIDENCE:
            self.logger.log("SHORT TRIGGERED", symbol=symbol, price=price, ema_fast=ema_fast, ema_slow=ema_slow, confidence=confidence)
            signal = "short"
        else:
            self.logger.log("No entry conditions met (signal=hold)", symbol=symbol, confidence=confidence)
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