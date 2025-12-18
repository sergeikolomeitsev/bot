# ============================================================
# VTR STRATEGY v10.6 — ФИЛЬТРЫ: strength, min_hold, N-confirm
# ============================================================

from typing import Dict, Any, List, Optional

class VTRStrategy:
    MIN_SIGNAL_STRENGTH = 0.15    # порог силы сигнала
    MIN_HOLD_BARS = 3             # минимум баров держим позицию
    N_CONFIRM = 2                 # число одинаковых сигналов подряд для подтверждения

    def __init__(self, portfolio, risk=1.0, analyzer=None):
        self.portfolio = portfolio
        self.analyzer = analyzer
        self.risk = risk
        self.bar_count = 0
        self.position_opened_at = {}       # symbol -> bar_opened
        self.last_signals = {}             # symbol -> [signal1, signal2, ...] (FIFO)

    @property
    def positions(self):
        return self.portfolio.positions

    @property
    def trades(self):
        return self.portfolio.trades

    def on_bar(self):
        """Вызывать это при каждом новом баре/time step (инкрементируем счетчик баров)."""
        self.bar_count += 1

    def open_position(self, symbol, price, amount, side="long"):
        self.portfolio.open_position(symbol, price, amount, side)
        self.position_opened_at[symbol] = self.bar_count

    def close_position(self, symbol, close_price=None):
        if not self.can_close_position(symbol):
            print(f"[VTRStrategy] Позу {symbol} нельзя закрыть — не выдержан min_hold!")
            return
        self.portfolio.close_position(symbol, close_price)
        self.position_opened_at.pop(symbol, None)

    def can_close_position(self, symbol):
        opened_at = self.position_opened_at.get(symbol)
        if opened_at is None:
            return True
        return (self.bar_count - opened_at) >= self.MIN_HOLD_BARS

    def calc_pnl(self, symbol, price):
        return self.portfolio.calc_pnl(symbol, price)

    def update_signal_buffer(self, symbol, current_signal):
        buf = self.last_signals.setdefault(symbol, [])
        buf.append(current_signal)
        if len(buf) > self.N_CONFIRM:
            buf.pop(0)
        # возвращает истину, если последние N_CONFIRM сигналов одинаковы и не hold
        return len(buf) == self.N_CONFIRM and len(set(buf)) == 1 and buf[-1] != "hold"

    def generate_signal(
        self,
        snapshot: Dict[str, Any],
        symbol: str,
        history: Optional[List[float]] = None
    ) -> Optional[Dict[str, Any]]:
        price = snapshot.get(symbol)
        if price is None or history is None or len(history) < 20 or self.analyzer is None:
            return None

        ema_fast = self.analyzer.ema(history, 5)
        ema_slow = self.analyzer.ema(history, 14)
        gap_val = self.analyzer.gap(history)

        if ema_fast is None or ema_slow is None or gap_val is None:
            return None

        signal = "hold"
        strength = 0.0

        # LONG logic (buy/open/hold long)
        if ema_fast > ema_slow and gap_val > 0:
            strength = float(abs(gap_val) * self.risk)
            if strength >= self.MIN_SIGNAL_STRENGTH:
                signal = "long"
        # SHORT logic (sell/open/hold short)
        elif ema_fast < ema_slow and gap_val < 0:
            strength = float(abs(gap_val) * self.risk)
            if strength >= self.MIN_SIGNAL_STRENGTH:
                signal = "short"

        # --- Фильтрация по N_CONFIRM ---
        confirmed = self.update_signal_buffer(symbol, signal)
        if not confirmed:
            # Требуем подтверждения N_CONFIRM раз подряд
            return {"symbol": symbol, "signal": "hold", "strength": 0.0}

        return {"symbol": symbol, "signal": signal, "strength": strength}

    def get_pnl(self, snapshot=None):
        """
        Возвращает pnl по реализованным и нереализованным позициям:
        {'realized': ..., 'unrealized': ...}
        """
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

    def on_market_data(self, market_data):
        pass