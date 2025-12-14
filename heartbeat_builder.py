# ============================================================
# HEARTBEAT BUILDER v9.7 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Генерирует расширенный статус:
# • Активная стратегия и её состояние (с описанием)
# • Freedom multiplier
# • Позиции и PnL (unrealized и realized)
# • Параметры индикаторов по каждому символу
# • Последние сигналы
# • Количество свечей истории
# ============================================================

from typing import Dict, Any

class HeartbeatBuilder:

    def __init__(self, di):
        """
        DI-container передается сюда для удобства:
        • market_data
        • trading_engine
        • ai_manager
        • portfolio
        • analyzer
        """
        self.di = di
        self.market = di.market_data
        self.engine = di.trading_engine
        self.portfolio = di.portfolio
        self.analyzer = di.analyzer
        self.ai = di.ai_manager
        self.cfg = di.config

    # ------------------------------------------------------------
    def build(self) -> str:

        symbols = self.cfg.trading.symbols
        snapshot = self.market.get_snapshot()

        out = []
        out.append("❤️ HEARTBEAT v9.7 — MARKET STATUS\n")

        # =====================================================
        # ACTIVE STRATEGY + ОПИСАНИЕ
        # =====================================================
        strategy = self.ai.get_active_strategy()
        strat_name = strategy.__class__.__name__ if strategy else "None"

        out.append("=== ACTIVE STRATEGY ===")
        out.append(f"• {strat_name} ({'Experimental' if self.ai.experimental_active else 'Base'})")
        out.append(f"• Freedom Multiplier: {self.di.freedom_manager.get_multiplier():.2f}")
        out.append(f"• A/B Testing: {'ON' if self.ai.experimental_active else 'OFF'}")
        # Добавим описание стратегии, если оно есть
        if strategy is not None:
            if hasattr(strategy, "description"):
                out.append(f"• {strategy.description}")
            elif hasattr(strategy, "get_description"):
                out.append(f"• {strategy.get_description()}")
        out.append("")

        # =====================================================
        # PORTFOLIO
        # =====================================================
        out.append("=== PORTFOLIO STATUS ===")
        positions = self.portfolio.positions

        if not positions:
            out.append("• No open positions\n")
        else:
            out.append(f"• Open positions: {len(positions)}")
            for sym, pos in positions.items():
                price = snapshot.get(sym)
                pnl = self.portfolio.calc_pnl(sym, price) if price else None
                out.append(
                    f"{sym} → entry {pos['entry_price']} | now {price} | PnL {pnl if pnl is not None else 'n/a'}"
                )
            # Добавить суммарный реализованный профит
            out.append(f"\n💰 Realized PnL (total): {self.portfolio.realized_pnl:.2f}\n")

        # =====================================================
        # TECHNICAL INDICATORS
        # =====================================================
        out.append("=== MARKET SNAPSHOT ===")

        for sym in symbols:
            hist = self.market.get_history(sym)
            if not hist or len(hist) < 20:
                out.append(f"{sym}: insufficient history ({len(hist) if hist else 0})")
                continue

            price = snapshot.get(sym)
            ema5 = self.analyzer.ema(hist, 5)
            ema20 = self.analyzer.ema(hist, 20)
            rsi = self.analyzer.rsi(hist, 14)
            gap = self.analyzer.gap(hist)
            vol = self.analyzer.volatility(hist)

            out.append(
                f"{sym}: {price} | EMA5 {ema5:.1f} | EMA20 {ema20:.1f} | "
                f"RSI {rsi:.0f} | GAP {gap:+.2f} | VOL {vol:.2f}"
            )

        out.append("")

        # =====================================================
        # SIGNALS
        # =====================================================
        out.append("=== SIGNALS ===")

        for sym in symbols:
            hist = self.market.get_history(sym)
            if not hist or len(hist) < 20:
                continue

            # получаем сигнал (без исполнения)
            result = self.engine.process(snapshot, sym, history=hist, return_explanation=False)
            if not result:
                continue

            signal = result.get("signal")
            strength = float(result.get("strength", 0))
            out.append(f"{sym} → {signal.upper()} ({strength:.2f})")

        out.append("")

        # =====================================================
        # HISTORY LENGTH
        # =====================================================
        out.append("=== HISTORY ===")
        for sym in symbols:
            out.append(f"{sym} candles stored: {len(self.market.get_history(sym))}")

        return "\n".join(out)