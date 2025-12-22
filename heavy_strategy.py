# ============================================================
# HEAVY STRATEGY v11.3 — TP/SL, trailing, ADX+ATR, risk/MM, комиссия,
# индивидуальный JSON-логгер (стратегии) + ДЕБАГ-ЛОГГЕР портфельных операций
# Более осторожная версия (ниже риск, выше фильтры, консервативнее вход)
# Совместим по логам и механике с VTRStrategy
# ============================================================

from debug_logger import DebugLogger

class HeavyStrategy:
    INIT_STACK = 300.0
    TAKE_PROFIT_PCT = 0.002  # было 0.004, теперь ниже
    STOP_LOSS_PCT = 0.001    # было 0.002, теперь ниже
    TRAILING_PCT = 0.001     # было 0.002, теперь ниже
    FEE_PCT = 0.0007
    SPREAD_PCT = 0.0005
    MAX_RISK_PCT = 0.02      # было 0.05, стал ниже риск
    MIN_RISK_PCT = 0.005     # минимальный риск ниже
    MIN_ADX = 18             # фильтр по тренду выше
    MIN_ATR_RATIO = 0.00009  # больше волатильности требуем
    MIN_CONFIDENCE = 0.06    # нужен больший confidence для входа

    def __init__(self, portfolio, analyzer=None, market=None):
        self.logger = DebugLogger("heavy_strategy_debug.json", max_records=10000)
        self.logger.enable()
        self.portfolio_logger = DebugLogger("heavy_portfolio_debug.json", max_records=10000)
        self.portfolio_logger.enable()

        self.portfolio = portfolio
        self.analyzer = analyzer
        self.market = market
        self.active_trades = {}
        self.balance = self.INIT_STACK
        self.in_market = set()
        self.last_signals = {}

        self.logger.log("strategy_initialized", balance=self.balance, active_trades=self.active_trades)

    @property
    def positions(self):
        self.logger.log("positions_requested")
        return self.portfolio.positions

    @property
    def trades(self):
        self.logger.log("trades_requested")
        return self.portfolio.trades

    def update_balance(self):
        self.logger.log("update_balance_called", current_balance=self.balance, init_stack=self.INIT_STACK)
        if not hasattr(self.portfolio, "trades"):
            self.logger.log("invalid_portfolio_object", error="No 'trades' attribute in portfolio")
            raise ValueError("Portfolio object does not have 'trades' attribute.")
        self.logger.log("portfolio_trades_details", trades=self.portfolio.trades)
        self.balance = self.INIT_STACK + sum([t.get("pnl", 0) for t in self.portfolio.trades])
        self.logger.log("update_balance_completed", updated_balance=self.balance)

    def can_trade(self):
        self.logger.log("can_trade_called", current_balance=self.balance, required_balance=self.INIT_STACK, active_trades=self.active_trades)
        self.update_balance()
        can_trade_result = self.balance >= 0.0
        self.portfolio_logger.log("can_trade_result", balance=self.balance, can_trade=can_trade_result, active_trades=self.active_trades)
        return can_trade_result

    def get_trade_amount(self, price, confidence):
        stack = self.balance
        pct = max(self.MIN_RISK_PCT, min(confidence, self.MAX_RISK_PCT))
        usdt = stack * pct
        trade_amount = max(round(usdt / price, 6), 0.0001)
        self.logger.log("trade_amount_calculated", price=price, confidence=confidence, trade_amount=trade_amount, balance=self.balance)
        return trade_amount

    def open_position(self, symbol, price, confidence, side):
        self.portfolio_logger.log("open_position_attempt", symbol=symbol, price=price, confidence=confidence, side=side)
        if not self.can_trade():
            self.portfolio_logger.log("open_position_blocked", symbol=symbol, reason="can_trade_returned_false", balance=self.balance, active_trades=self.active_trades)
            return
        if symbol in self.active_trades:
            self.portfolio_logger.log("open_position_blocked", symbol=symbol, reason="already_active", active_trades=list(self.active_trades.keys()))
            return
        amount = self.get_trade_amount(price, confidence)
        fee = self.FEE_PCT + self.SPREAD_PCT
        tp = price * (1 + self.TAKE_PROFIT_PCT - fee) if side == "long" else price * (1 - self.TAKE_PROFIT_PCT + fee)
        sl = price * (1 - self.STOP_LOSS_PCT - fee) if side == "long" else price * (1 + self.STOP_LOSS_PCT + fee)
        trailing = self.TRAILING_PCT * price

        # -=--------- ВОТ ЭТА СТРОКА СНЯТИЯ ДЕНЕГ С БАЛАНСА:
        cost = amount * price * (1 + self.FEE_PCT + self.SPREAD_PCT)
        self.balance -= cost
        self.logger.log("balance_decreased_on_open", balance=self.balance, cost=cost, symbol=symbol, amount=amount,
                        price=price)

        self.portfolio_logger.log("open_position_details", amount=amount, tp=tp, sl=sl, trailing=trailing)
        self.portfolio.open_position(
            symbol, price, amount, side,
            tp=tp, sl=sl, trailing_extremum=trailing
        )
        self.active_trades[symbol] = {
            "entry": price,
            "amount": amount,
            "side": side,
            "tp": tp,
            "sl": sl,
            "trailing": trailing,
            "extremum": price,
        }
        self.portfolio_logger.log("open_position_success", symbol=symbol, price=price, amount=amount, side=side, confidence=confidence, tp=tp, sl=sl, trailing=trailing)

    def close_position(self, symbol, price):
        self.portfolio_logger.log("close_position_attempt", symbol=symbol, price=price)
        if symbol not in self.active_trades:
            self.portfolio_logger.log("close_position_blocked", symbol=symbol, reason="not_active", active_trades=self.active_trades)
            return
        self.portfolio.close_position(symbol, price)
        self.active_trades.pop(symbol, None)
        self.in_market.discard(symbol)
        self.update_balance()
        self.portfolio_logger.log("close_position_success", symbol=symbol, price=price, balance=self.balance)

    def on_tick(self, snapshot):
        self.logger.log("on_tick_called", snapshot=snapshot, active_trades=self.active_trades)
        for symbol, trade in list(self.active_trades.items()):
            price = snapshot.get(symbol)
            if not price:
                self.logger.log("on_tick_price_missing", symbol=symbol)
                continue
            if trade["side"] == "long":
                if price > trade["extremum"]:
                    trade["extremum"] = price
                stop = trade["extremum"] - trade["trailing"]
                self.logger.log("on_tick_long_trade_evaluated", symbol=symbol, price=price, stop=stop, tp=trade["tp"], sl=trade["sl"])
                if price <= stop or price >= trade["tp"] or price <= trade["sl"]:
                    self.close_position(symbol, price)
            else:
                if price < trade["extremum"]:
                    trade["extremum"] = price
                stop = trade["extremum"] + trade["trailing"]
                self.logger.log("on_tick_short_trade_evaluated", symbol=symbol, price=price, stop=stop, tp=trade["tp"], sl=trade["sl"])
                if price >= stop or price <= trade["tp"] or price >= trade["sl"]:
                    self.close_position(symbol, price)
        # Генерация сигналов для новых символов
        for symbol, price in snapshot.items():
            if symbol not in self.active_trades:
                history = None
                if self.market is not None:
                    history = self.market.get_history(symbol)
                signal = self.generate_signal(snapshot, symbol, history=history)
                if signal and signal["signal"] in {"long", "short"}:
                    self.open_position(symbol, price, signal["strength"], signal["signal"])

    def generate_signal(self, snapshot, symbol, history=None):
        history = history if history is not None else []
        self.logger.log("generate_signal_called", symbol=symbol, len_history=len(history))
        if symbol in self.active_trades:
            self.logger.log("generate_signal_skipped", reason="already_active", symbol=symbol)
            return None
        if not history:
            self.logger.log("generate_signal_skipped", reason="history_missing", symbol=symbol)
            return None
        if len(history) < 30:
            self.logger.log("generate_signal_skipped", reason="insufficient_history", symbol=symbol,
                            history_length=len(history))
            return None
        if not self.analyzer:
            self.logger.log("generate_signal_skipped", reason="no_analyzer", symbol=symbol)
            return None

        highs = [bar["high"] for bar in history]
        lows = [bar["low"] for bar in history]
        closes = [bar["close"] for bar in history]
        price = closes[-1]

        ema_fast = self.analyzer.ema(closes, 7)
        ema_slow = self.analyzer.ema(closes, 25)
        adx_val = self.analyzer.adx(highs, lows, closes, 14)
        atr_val = self.analyzer.atr(highs, lows, closes, 14)
        rsi_val = self.analyzer.rsi(closes, 14)

        self.logger.log("indicators_calculated", symbol=symbol, price=price, ema_fast=ema_fast, ema_slow=ema_slow, adx=adx_val, atr=atr_val, rsi=rsi_val)

        if None in (ema_fast, ema_slow, adx_val, atr_val, rsi_val):
            self.logger.log("missing_indicators", symbol=symbol)
            return None

        if adx_val < self.MIN_ADX or atr_val / price < self.MIN_ATR_RATIO:
            self.logger.log("filter_failed", symbol=symbol, adx=adx_val, atr=atr_val, price=price)
            return {"symbol": symbol, "signal": "hold", "strength": 0.0}

        confidence = min((adx_val - self.MIN_ADX) * 0.07 + 0.03, self.MAX_RISK_PCT)
        self.logger.log("confidence_calculated", symbol=symbol, confidence=confidence, min_confidence=self.MIN_CONFIDENCE)

        signal = "hold"
        if ema_fast > ema_slow and confidence >= self.MIN_CONFIDENCE:
            self.logger.log("long_signal", symbol=symbol, price=price, confidence=confidence)
            signal = "long"
        elif ema_fast < ema_slow and confidence >= self.MIN_CONFIDENCE:
            self.logger.log("short_signal", symbol=symbol, price=price, confidence=confidence)
            signal = "short"
        else:
            self.logger.log("signal_hold", symbol=symbol, confidence=confidence)
        self.logger.log("generate_signal_result", symbol=symbol, signal=signal, confidence=confidence)

        return {"symbol": symbol, "signal": signal, "strength": confidence}

    def get_pnl(self, snapshot=None):
        realized = sum([t.get("pnl", 0) for t in self.trades])
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
        self.logger.log("get_pnl_called", realized=realized, unrealized=unrealized)
        return {"realized": realized, "unrealized": unrealized}