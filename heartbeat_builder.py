# ============================================================
# HEARTBEAT BUILDER v11.2 — PnL для каждой позиции
# ============================================================

from typing import List


class HeartbeatBuilder:
    def __init__(self, di, baseline_strategy, experimental_strategy):
        self.di = di
        self.market = di.market_data
        self.baseline_strategy = baseline_strategy
        self.experimental_strategy = experimental_strategy
        self.cfg = di.config

    def build(self):
        out = []
        out.append("❤️ HEARTBEAT v11.2 — PARALLEL AB TEST\n")

        # === BASELINE STRATEGY ===
        baseline = self.baseline_strategy
        out.append("=== BASELINE STRATEGY ===")
        out.append(f"• Класс: {baseline.__class__.__name__}")

        snapshot = self.market.get_snapshot()
        base_pnl = baseline.get_pnl(snapshot)
        out.append(f"• Realized: {base_pnl['realized']:.2f} | Unrealized: {base_pnl['unrealized']:.2f}")
        positions = getattr(baseline, "positions", {})
        if not positions:
            out.append("• No open positions")
        else:
            out.append(f"• Open positions: {len(positions)}")
            for sym, pos in positions.items():
                price = snapshot.get(sym)
                pnl = None
                if hasattr(baseline, "calc_pnl"):
                    try:
                        if price is not None:
                            pnl = baseline.calc_pnl(sym, price)
                    except Exception:
                        pnl = None
                if pnl is not None:
                    out.append(
                        f"{sym} [{pos.get('side','long')}] → entry {pos['entry_price']} | now {price} | PnL {pnl:.2f}"
                    )
                else:
                    out.append(
                        f"{sym} [{pos.get('side','long')}] → entry {pos['entry_price']} | now {price}"
                    )
        out.append("")

        # === EXPERIMENTAL STRATEGY ===
        experimental = self.experimental_strategy
        out.append("=== EXPERIMENTAL STRATEGY ===")
        out.append(f"• Класс: {experimental.__class__.__name__}")

        exp_pnl = experimental.get_pnl(snapshot)
        out.append(f"• Realized: {exp_pnl['realized']:.2f} | Unrealized: {exp_pnl['unrealized']:.2f}")
        positions = getattr(experimental, "positions", {})
        if not positions:
            out.append("• No open positions")
        else:
            out.append(f"• Open positions: {len(positions)}")
            for sym, pos in positions.items():
                price = snapshot.get(sym)
                pnl = None
                if hasattr(experimental, "calc_pnl"):
                    try:
                        if price is not None:
                            pnl = experimental.calc_pnl(sym, price)
                    except Exception:
                        pnl = None
                if pnl is not None:
                    out.append(
                        f"{sym} [{pos.get('side','long')}] → entry {pos['entry_price']} | now {price} | PnL {pnl:.2f}"
                    )
                else:
                    out.append(
                        f"{sym} [{pos.get('side','long')}] → entry {pos['entry_price']} | now {price}"
                    )
        out.append("")

        # === MARKET SNAPSHOT ===
        symbols = list(self.market.history.keys())
        out.append("=== MARKET SNAPSHOT ===")
        for sym in symbols:
            hist = self.market.get_history(sym)
            if not hist or len(hist) < 20:
                out.append(f"{sym}: insufficient history ({len(hist) if hist else 0})")
            else:
                out.append(f"{sym}: history ok ({len(hist)})")
        out.append("")

        return "\n".join(out)

    def send(self):
        text = self.build()
        bot = getattr(self.di, "telegram_bot", None)
        if bot is not None and hasattr(bot, "send_heartbeat"):
            return bot.send_heartbeat(text)
        else:
            raise RuntimeError("telegram_bot не настроен или не поддерживает send_heartbeat")