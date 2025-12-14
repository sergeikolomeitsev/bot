# ============================================================
# TRADING LOOP v10.1 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Основной торговый цикл:
# - Получает market_data из WSPriceFeed (Bybit Spot, стабильный reconnect)
# - Проверяет отзывчивость feed и dead-feed
# - Для каждого тикера вызывает ABTestingEngine (две стратегии: базовая и экспериментальная)
# - Каждую минуту отправляет heartbeat
# - Интеграция с Telegram для алертов
# - Не сбрасывает историю, всё пишет в JSON
# ------------------------------------------------------------
# Версия 10.1:
# ! ВАЖНО: для поддержки DI (dependency_container.py) добавлен класс TradingLoop,
#   не затронута процедурная main(), логика не ломается.
# ! Корректно прокидывает config, ab_engine, Telegram, heartbeat (по DI-контейнеру).
# ! procedural main() также поддержан для самостоятельного запуска.
# ============================================================

import time
import logging

from ab_testing_engine import ABTestingEngine
from ws_price_feed import WSPriceFeed
from config import config
# from telegram_bot import TelegramBot
# from heartbeat_builder import HeartbeatBuilder

logger = logging.getLogger("TradingLoop")


class TradingLoop:
    def __init__(self, config=config, ab_engine=None, telegram_bot=None, heartbeat=None):
        self.config = config
        self.price_feed = WSPriceFeed(config)
        self.ab_engine = ab_engine if ab_engine is not None else ABTestingEngine(initial_balance=300)
        self.telegram_bot = telegram_bot
        self.heartbeat = heartbeat

    def run(self):
        logger.info("== TRADING LOOP v10.1: STARTED (class-mode, DI compatible) ==")
        dead_feed_alerted = False
        last_heartbeat = 0

        while True:
            feed_alive = self.price_feed.is_alive()
            now = time.time()

            # Проверка жив ли feed: аварийное оповещение если нет обновлений
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

            # Получаем валидные цены (по всем тикерам одновременно)
            prices = self.price_feed.get_prices()
            if not prices:
                time.sleep(1)
                continue

            # Для каждого тикера — передача market_data обеим стратегиям через ab_engine
            for symbol, price in prices.items():
                market_data = {
                    'symbol': symbol,
                    'price': price,
                    'timestamp': now
                    # Другие параметры по необходимости (например, объем, bid/ask и т.д.)
                }
                self.ab_engine.on_market_data(market_data)
                # Внутри ab_engine сама формируется история и делаются отчёты каждый час/день

            # Ежеминутный heartbeat для мониторинга (можно отправлять ботом)
            if now - last_heartbeat > 60:
                logger.info("HEARTBEAT: system alive, feed ok")
                if self.heartbeat:
                    self.heartbeat.send()
                last_heartbeat = now

            time.sleep(1)


def main():
    logger.info("== TRADING LOOP v10.1: STARTED (procedural mode) ==")
    # Инициализация компонентов: классический procedural запуск (без DI container)
    price_feed = WSPriceFeed(config)
    ab_engine = ABTestingEngine(initial_balance=300)
    # bot = TelegramBot(config)                 # при необходимости
    # heartbeat = HeartbeatBuilder()            # при необходимости

    dead_feed_alerted = False
    last_heartbeat = 0

    while True:
        feed_alive = price_feed.is_alive()
        now = time.time()

        if not feed_alive:
            if not dead_feed_alerted:
                logger.error("❌ Price Feed DEAD, no updates — check connection!")
                # bot.send_alert("❌ WS Price Feed DEAD, no updates!")   # если интегрирован Telegram
                dead_feed_alerted = True
            time.sleep(5)
            continue
        else:
            if dead_feed_alerted:
                logger.info("✅ Price Feed restored.")
                # bot.send_alert("✅ Price Feed restored!")             # если интегрирован Telegram
                dead_feed_alerted = False

        prices = price_feed.get_prices()
        if not prices:
            time.sleep(1)
            continue

        for symbol, price in prices.items():
            market_data = {
                'symbol': symbol,
                'price': price,
                'timestamp': now
            }
            ab_engine.on_market_data(market_data)

        if now - last_heartbeat > 60:
            logger.info("HEARTBEAT: system alive, feed ok")
            # heartbeat.send()        # при необходимости
            last_heartbeat = now

        time.sleep(1)


if __name__ == '__main__':
    main()