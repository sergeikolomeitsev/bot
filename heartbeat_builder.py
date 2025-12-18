# ============================================================
# HEARTBEAT BUILDER v11.3 — сделки за сутки вместо "open positions"
# ============================================================

class HeartbeatBuilder:
    def __init__(self, di, baseline_strategy, experimental_strategy):
        self.di = di
        self.market = di.market_data
        self.baseline_strategy = baseline_strategy
        self.experimental_strategy = experimental_strategy
        self.cfg = di.config

    def build(self):
        out = []
        out.append("❤️ HEARTBEAT v11.3 — PARALLEL AB TEST\n")

        # === BASELINE STRATEGY ===
        baseline = self.baseline_strategy
        out.append("=== BASELINE STRATEGY ===")
        out.append(f"• Класс: {baseline.__class__.__name__}")

        snapshot = self.market.get_snapshot()
        base_pnl = baseline.get_pnl(snapshot)
        out.append(f"• Realized: {base_pnl['realized']:.2f} | Unrealized: {base_pnl['unrealized']:.2f}")

        # Суточная статистика по сделкам:
        baseline_portfolio = getattr(baseline, "portfolio", None)
        if baseline_portfolio and hasattr(baseline_portfolio, "trades_today_stats"):
            total, win, loss = baseline_portfolio.trades_today_stats()
            out.append(f"• Сделок за сегодня: всего={total} | успешных={win} | неуспешных={loss}")
        else:
            out.append("• Нет данных по сделкам за сегодня")

        # По-прежнему можно распечатать список активных позиций при желании (вариант):
        positions = getattr(baseline, "positions", {})
        if positions:
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

        experimental_portfolio = getattr(experimental, "portfolio", None)
        if experimental_portfolio and hasattr(experimental_portfolio, "trades_today_stats"):
            total, win, loss = experimental_portfolio.trades_today_stats()
            out.append(f"• Сделок за сегодня: всего={total} | успешных={win} | неуспешных={loss}")
        else:
            out.append("• Нет данных по сделкам за сегодня")

        positions = getattr(experimental, "positions", {})
        if positions:
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