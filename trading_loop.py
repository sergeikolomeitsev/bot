# ============================================================
# TRADING LOOP v9.6 — final fix (NO portfolio.execute)
# ============================================================

import logging
import time
from datetime import datetime


class TradingLoop:

    def __init__(self, config, market_data_manager, strategy_engine, portfolio_service, telegram_bot):
        self.logger = logging.getLogger("TradingLoop")

        self.cfg = config
        self.market = market_data_manager
        self.strategy = strategy_engine
        self.portfolio = portfolio_service
        self.bot = telegram_bot

        self.interval = config.trading.trading_cycle_seconds
        self.snapshot_interval = config.trading.snapshot_interval_seconds
        self.last_snapshot_log = None

        self.logger.info(
            f"🔁 TradingLoop v9.6 initialized | cycle={self.interval}s | snapshot={self.snapshot_interval}s"
        )

    # =====================================================================
    def run(self, symbols):
        self.logger.info("▶️ TradingLoop started")

        while True:
            cycle_start = time.time()

            updated = self.market.update()
            if not updated:
                self.logger.warning("⚠ No fresh WS data — skipping cycle.")
                time.sleep(self.interval)
                continue

            if not self.market.ws.is_alive():
                self.logger.error("🛑 Dead-feed detected")
                time.sleep(self.interval)
                continue

            snapshot = self.market.get_snapshot()
            if not snapshot:
                self.logger.warning("⚠ Empty snapshot — skipping.")
                time.sleep(self.interval)
                continue

            now = datetime.now()
            if (
                self.last_snapshot_log is None or
                (now - self.last_snapshot_log).total_seconds() >= self.snapshot_interval
            ):
                formatted = ", ".join(f"{s}: {snapshot[s]}" for s in snapshot)
                self.logger.info(f"📸 Snapshot: {formatted}")
                self.last_snapshot_log = now

            # ------------------------------------------------------------
            # STRATEGY & PORTFOLIO EXECUTION
            # ------------------------------------------------------------
            try:
                for sym, price in snapshot.items():

                    history = self.market.get_history(sym)
                    decision = self.strategy.process(snapshot, sym, history)
                    if not decision:
                        continue

                    signal = decision.get("signal", "hold")
                    strength = float(decision.get("strength", 0))

                    # BUY
                    if signal == "buy":
                        if not self.portfolio.get_position(sym):
                            self.portfolio.open_position(sym, price, strength)

                    # SELL
                    elif signal == "sell":
                        if self.portfolio.get_position(sym):
                            self.portfolio.close_position(sym)

                    # HOLD — do nothing

            except Exception as e:
                self.logger.error(f"❌ Strategy/Portfolio error inside loop: {e}")

            elapsed = time.time() - cycle_start
            time.sleep(max(0, self.interval - elapsed))
