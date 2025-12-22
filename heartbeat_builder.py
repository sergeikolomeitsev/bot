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
        print("[DEBUG] HB VTRStrategy id:", id(self.experimental_strategy))
        print("[DEBUG] HB Portfolio id:", id(self.experimental_strategy.portfolio))
        # Для baseline тоже, если нужно:
        print("[DEBUG] HB HeavyStrategy id:", id(self.baseline_strategy))
        print("[DEBUG] HB Portfolio (baseline) id:", id(self.baseline_strategy.portfolio))
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
        trades = []
        if baseline_portfolio and hasattr(baseline_portfolio, "trades"):
            trades = baseline_portfolio.trades

        positions = getattr(baseline, "positions", {})

        # --- НОВЫЙ БЛОК ДЛЯ BASELINE ---
        # Собираем все символы, по которым были сделки в истории или есть открытые позиции
        all_trade_syms = set(t.get("symbol") for t in trades)
        all_pos_syms = set(positions.keys())
        all_syms = sorted(all_trade_syms | all_pos_syms)

        for sym in all_syms:
            pos = positions.get(sym)
            pnl_real = sum(t.get("pnl", 0.0) for t in trades if t.get("symbol") == sym)
            if pos:
                price = snapshot.get(sym)
                qty = pos.get("amount")
                tp = pos.get("tp")
                sl = pos.get("sl")
                trailing = pos.get("trailing_extremum")
                side = pos.get("side", "long")
                pnl_unreal = 0.0
                if hasattr(baseline, "portfolio") and baseline.portfolio:
                    try:
                        if price is not None:
                            pnl_unreal = baseline.portfolio.calc_pnl(sym, price)
                    except Exception:
                        pass
                out.append(
                    f"{sym} [{side}] qty={qty} → entry {pos['entry_price']} | now {price}"
                    f" | TP={tp} SL={sl} trailing={trailing}"
                    f" | PnL unreal: {pnl_unreal:.4f} PnL real: {pnl_real:.4f}"
                )
            else:
                out.append(f"{sym} [открытых сделок нет] | PnL real: {pnl_real:.4f}")
        out.append("")

        # Добавим баланс baseline:
        current_baseline_balance = getattr(baseline, "balance", None)
        if current_baseline_balance is not None:
            out.append(f"• Баланс: {current_baseline_balance:.2f}")
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

        trades_exp = []
        if experimental_portfolio and hasattr(experimental_portfolio, "trades"):
            trades_exp = experimental_portfolio.trades

        positions = getattr(experimental, "positions", {})
        # --- НОВЫЙ БЛОК СТАРТ ---
        # Соберём все символы, по которым были сделки (могут быть как с позициями, так и без)
        all_trade_syms = set(t.get("symbol") for t in trades_exp)
        all_pos_syms = set(positions.keys())
        all_syms = sorted(all_trade_syms | all_pos_syms)

        for sym in all_syms:
            pos = positions.get(sym)
            pnl_real = sum(t.get("pnl", 0.0) for t in trades_exp if t.get("symbol") == sym)
            if pos:
                price = snapshot.get(sym)
                qty = pos.get("amount")
                tp = pos.get("tp")
                sl = pos.get("sl")
                trailing = pos.get("trailing_extremum")
                side = pos.get("side", "long")
                pnl_unreal = 0.0
                if hasattr(experimental, "portfolio") and experimental.portfolio:
                    try:
                        if price is not None:
                            pnl_unreal = experimental.portfolio.calc_pnl(sym, price)
                    except Exception:
                        pass
                out.append(
                    f"{sym} [{side}] qty={qty} → entry {pos['entry_price']} | now {price}"
                    f" | TP={tp} SL={sl} trailing={trailing}"
                    f" | PnL unreal: {pnl_unreal:.4f} PnL real: {pnl_real:.4f}"
                )
            else:
                out.append(f"{sym} [открытых сделок нет] | PnL real: {pnl_real:.4f}")
        out.append("")

        # Добавим баланс experimental:
        current_exp_balance = getattr(experimental, "balance", None)
        if current_exp_balance is not None:
            out.append(f"• Баланс: {current_exp_balance:.2f}")
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