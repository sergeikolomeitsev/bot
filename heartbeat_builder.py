# ============================================================
# HEARTBEAT BUILDER v11.0 — Parallel AB test heartbeat
# ------------------------------------------------------------
# Показывает статистику baseline и experimental стратегий одновременно.
# ============================================================

from typing import Dict, Any

class HeartbeatBuilder:

    def __init__(self, di):
        self.di = di
        self.market = di.market_data
        self.engine = di.trading_engine
        self.ai = di.ai_manager
        self.cfg = di.config

    # ------------------------------------------------------------
    def build(self) -> str:
        symbols = self.cfg.trading.symbols
        snapshot = self.market.get_snapshot()

        out = []
        out.append("❤️ HEARTBEAT v11.0 — PARALLEL AB TEST\n")

        # === BASELINE STRATEGY STATUS ===
        baseline = self.ai.baseline_strategy
        out.append("=== BASELINE STRATEGY ===")
        out.append(f"• {baseline.__class__.__name__}")
        base_pnl = baseline.get_pnl()
        out.append(f"• Realized: {base_pnl['realized']:.2f} | Unrealized: {base_pnl['unrealized']:.2f}")
        positions = baseline.positions
        if not positions:
            out.append("• No open positions")
        else:
            out.append(f"• Open positions: {len(positions)}")
            for sym, pos in positions.items():
                price = snapshot.get(sym)
                pnl = baseline.calc_pnl(sym, price) if price else None
                out.append(
                    f"{sym} → entry {pos['entry_price']} | now {price} | PnL {pnl if pnl is not None else 'n/a'}"
                )
        out.append("")

        # === EXPERIMENTAL STRATEGY STATUS ===
        experimental = self.ai.experimental_strategy
        out.append("=== EXPERIMENTAL STRATEGY ===")
        out.append(f"• {experimental.__class__.__name__}")
        exp_pnl = experimental.get_pnl()
        out.append(f"• Realized: {exp_pnl['realized']:.2f} | Unrealized: {exp_pnl['unrealized']:.2f}")
        positions = experimental.positions
        if not positions:
            out.append("• No open positions")
        else:
            out.append(f"• Open positions: {len(positions)}")
            for sym, pos in positions.items():
                price = snapshot.get(sym)
                pnl = experimental.calc_pnl(sym, price) if price else None
                out.append(
                    f"{sym} → entry {pos['entry_price']} | now {price} | PnL {pnl if pnl is not None else 'n/a'}"
                )
        out.append("")

        # === MARKET SNAPSHOT ===
        out.append("=== MARKET SNAPSHOT ===")
        for sym in symbols:
            hist = self.market.get_history(sym)
            if not hist or len(hist) < 20:
                out.append(f"{sym}: insufficient history ({len(hist) if hist else 0})")
            else:
                out.append(f"{sym}: history ok ({len(hist)})")
        out.append("")

        # === HISTORY (по обеим стратегиями)
        out.append("=== HISTORY ===")
        for sym in symbols:
            hist = self.market.get_history(sym)
            out.append(f"{sym} candles stored: {len(hist) if hist else 0}")

        return "\n".join(out)

    def send(self):
        text = self.build()
        bot = getattr(self.di, "telegram_bot", None)
        if bot is not None and hasattr(bot, "send_heartbeat"):
            return bot.send_heartbeat(text)
        else:
            raise RuntimeError("telegram_bot не настроен или не поддерживает send_heartbeat")