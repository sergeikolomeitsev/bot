# ============================================================
# HEARTBEAT BUILDER v11.1 — Parallel AB test heartbeat
# ------------------------------------------------------------
# Новый heartbeat: Показывает baseline и experimental стратегии, их PnL, позиции, сигналы.
# Полное live-сравнение для A/B теста.
# ============================================================

from typing import Dict, Any

class HeartbeatBuilder:

    def __init__(self, di):
        self.di = di
        self.market = di.market_data
        self.ai = di.ai_manager
        self.cfg = di.config

    def build(self) -> str:
        symbols = self.cfg.trading.symbols
        snapshot = self.market.get_snapshot()

        out = []
        out.append("❤️ HEARTBEAT v11.1 — PARALLEL AB TEST\n")

        # === BASELINE STRATEGY ===
        baseline = self.ai.baseline_strategy
        out.append("=== BASELINE STRATEGY ===")
        out.append(f"• Класс: {baseline.__class__.__name__}")

        base_pnl = baseline.get_pnl()
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
                        pnl = baseline.calc_pnl(sym, price) if price else None
                    except Exception:
                        pnl = None
                out.append(
                    f"{sym} [{pos.get('side','long')}] → entry {pos['entry_price']} | now {price} | PnL {pnl if pnl is not None else 'n/a'}"
                )
        out.append("")

        # === EXPERIMENTAL STRATEGY ===
        experimental = self.ai.experimental_strategy
        out.append("=== EXPERIMENTAL STRATEGY ===")
        out.append(f"• Класс: {experimental.__class__.__name__}")

        exp_pnl = experimental.get_pnl()
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
                        pnl = experimental.calc_pnl(sym, price) if price else None
                    except Exception:
                        pnl = None
                out.append(
                    f"{sym} [{pos.get('side','long')}] → entry {pos['entry_price']} | now {price} | PnL {pnl if pnl is not None else 'n/a'}"
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

        # === HISTORY (по обеим стратегиям)
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