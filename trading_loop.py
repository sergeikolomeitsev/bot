# ============================================================
# TRADING LOOP v11.1 — Parallel AB test (live, buffered history)
# ------------------------------------------------------------
# Для каждого тикера обе стратегии обновляют портфели/статистику.
# MarketDataManager аккумулирует историю цен (для heartbeat/стратегий).
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
        logger.info("== TRADING LOOP v11.1: STARTED — Parallel AB test ==")
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

            # Теперь работаем всегда с market_data — правильно наполняется history!
            market_snapshot = self.market_data.get_snapshot()
            for symbol, price in market_snapshot.items():
                history = self.market_data.get_history(symbol)
                single_market_data = {
                    "snapshot": market_snapshot,
                    "symbol": symbol,
                    "history": history
                }
                self.ab_engine.on_market_data(single_market_data, freedom=1.0)

            # heartbeat раз в 300 сек
            if self.heartbeat and (now - last_heartbeat > 300):
                self.heartbeat.send()
                last_heartbeat = now

            time.sleep(1)