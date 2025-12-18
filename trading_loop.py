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
from market_data_manager import MarketDataManager  # АККУРАТНО добавлен импорт

logger = logging.getLogger("TradingLoop")

class TradingLoop:
    def __init__(self,
                 config=config,
                 ab_engine=None,
                 telegram_bot=None,
                 heartbeat=None,
                 market_data=None):
        self.config = config
        self.price_feed = WSPriceFeed(config)
        self.ab_engine = ab_engine if ab_engine is not None else ABTestingEngine(config, initial_balance=300)
        self.telegram_bot = telegram_bot
        self.heartbeat = heartbeat
        self.market_data = market_data

    def run(self):
        logger.info("== TRADING LOOP v11.2: STARTED — Parallel AB test ==")
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
            for symbol, price in market_snapshot.items():
                history = self.market_data.get_history(symbol)
                for strat_name, strategy in strategies:
                    sig = strategy.generate_signal(market_snapshot, symbol, history)
                    if sig is None:
                        logger.debug(f"[{strat_name}] [{symbol}] No signal generated")
                        continue
                    signal = sig.get("signal")
                    strength = sig.get("strength", 0.0)
                    pos = strategy.positions.get(symbol)
                    # Открытие/закрытие позиций на основе сигнала
                    if signal == "long":
                        if not pos or pos.get("side") != "long":
                            if pos:
                                logger.info(f"[{strat_name}] [{symbol}] Closing {pos['side']} to open LONG")
                                strategy.close_position(symbol, price)
                            logger.info(f"[{strat_name}] [{symbol}] Opening LONG at {price}")
                            strategy.open_position(symbol, price, amount=strength, side="long")
                    elif signal == "short":
                        if not pos or pos.get("side") != "short":
                            if pos:
                                logger.info(f"[{strat_name}] [{symbol}] Closing {pos['side']} to open SHORT")
                                strategy.close_position(symbol, price)
                            logger.info(f"[{strat_name}] [{symbol}] Opening SHORT at {price}")
                            strategy.open_position(symbol, price, amount=strength, side="short")
                    elif signal == "hold":
                        logger.debug(f"[{strat_name}] [{symbol}] Holding position")
                    else:
                        logger.warning(f"[{strat_name}] [{symbol}] Unknown signal: {signal}")

            # heartbeat раз в 300 сек
            if self.heartbeat and (now - last_heartbeat > 300):
                self.heartbeat.send()
                last_heartbeat = now

            time.sleep(1)