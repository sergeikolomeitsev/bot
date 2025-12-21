# ============================================================
# TRADING LOOP v11.2 — Parallel AB test (live, buffered history, per-strategy-processing)
# ------------------------------------------------------------
# Для каждого тикера обе стратегии обновляют портфели/статистику.
# MarketDataManager аккумулирует историю цен (для heartbeat/стратегий).
# Теперь ГАРАНТИРОВАН вызов обработки для каждой стратегии и каждого тикера.
# ============================================================

import time
import logging

from ab_testing_engine import ABTestingEngine
from ws_price_feed import WSPriceFeed
from config import config

logger = logging.getLogger("TradingLoop")

class TradingLoop:
    def __init__(self,
                 config,
                 ab_engine,         # ← больше нет значения по умолчанию!
                 telegram_bot=None,
                 heartbeat=None,
                 market_data=None,
                 analyzer=None):
        self.config = config
        self.price_feed = WSPriceFeed(config)
        if ab_engine is None:
            raise ValueError("TradingLoop должен быть инициализирован с существующим ab_engine! (DI)")
        self.ab_engine = ab_engine  # <-- только через DI!
        self.telegram_bot = telegram_bot
        self.heartbeat = heartbeat
        self.market_data = market_data

    def run(self):
        logger.info("== TRADING LOOP v11.2: STARTED — Parallel AB test ==")
        try:
            print("[DEBUG] TradingLoop VTRStrategy id:", id(self.ab_engine.experimental_strategy))
            print("[DEBUG] TradingLoop Portfolio id:", id(self.ab_engine.experimental_strategy.portfolio))
            print("[DEBUG] TradingLoop HeavyStrategy id:", id(self.ab_engine.baseline_strategy))
            print("[DEBUG] TradingLoop Portfolio (baseline) id:", id(self.ab_engine.baseline_strategy.portfolio))
        except Exception as e:
            print("[DEBUG] TradingLoop id print error:", e)
        dead_feed_alerted = False
        last_heartbeat = 0

        while True:
            feed_alive = self.price_feed.is_alive()
            now = time.time()

            if not feed_alive:
                if not dead_feed_alerted:
                    logger.error("❌ Price Feed DEAD, no updates — check connection!")
                    if self.telegram_bot:
                        self.telegram_bot.send_alert("❌ WS Price Feed DEAD, no updates!")
                    dead_feed_alerted = True
                time.sleep(5)
                continue
            else:
                if dead_feed_alerted:
                    logger.info("✅ Price Feed restored.")
                    if self.telegram_bot:
                        self.telegram_bot.send_alert("✅ Price Feed restored!")
                    dead_feed_alerted = False

            # ------------------------
            # Вот тут вся нежность: обновляем исторический буфер
            self.market_data.update()

            # ГАРАНТИРОВАННЫЙ вызов обработки для КАЖДОГО тикера и КАЖДОЙ стратегии:
            market_snapshot = self.market_data.get_snapshot()
            baseline_strategy = self.ab_engine.baseline_strategy
            experimental_strategy = self.ab_engine.experimental_strategy
            strategies = [
                ("baseline", baseline_strategy),
                ("experimental", experimental_strategy)
            ]

            for strat_name, strategy in strategies:
                strategy.on_tick(market_snapshot)  # стратегия сама обрабатывает TP/SL/trailing/etc

            # --- [ PATCH: автоматическое открытие позиции по сигналу ] ---
            for symbol, price in market_snapshot.items():
                history = self.market_data.get_history(symbol)
                for strat_name, strategy in strategies:
                    sig = strategy.generate_signal(market_snapshot, symbol, history)
                    # Считаем, что "signal" должен быть long или short И сигнальный confidence/strength должен присутствовать
                    if (
                            sig
                            and sig.get("signal") in ("long", "short")
                            and symbol not in strategy.active_trades
                    ):
                        confidence = sig.get("confidence", sig.get("strength"))
                        logger.info(
                            f"[{strat_name}] Opening position: {symbol} side={sig['signal']} conf={confidence}"
                        )
                        strategy.open_position(symbol, price, confidence, sig["signal"])

            # heartbeat раз в 300 сек
            if self.heartbeat and (now - last_heartbeat > 300):
                self.heartbeat.send()
                last_heartbeat = now

            time.sleep(1)