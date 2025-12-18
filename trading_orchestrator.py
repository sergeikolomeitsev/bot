# ============================================================
# TRADING ORCHESTRATOR v9.2 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Поддержка мульти-символьного TradingLoop:
# - запускает один главный цикл TradingLoop
# - передаёт в цикл полный список монет
# ============================================================

import logging
import traceback
import threading, time
from datetime import datetime

class TradingOrchestrator:
    """
    Высокоуровневый контроллер.
    Управляет безопасным запуском торгового цикла.
    """

    def __init__(self, config, di_container):
        self.cfg = config
        self.di = di_container
        self.loop = di_container.get_loop()
        self.bot = di_container.telegram_bot

        self.logger = logging.getLogger("Orchestrator")

    # ------------------------------------------------------------
    # PUBLIC — START TRADING
    # ------------------------------------------------------------
    def start(self):
        """
        Запускает торговый цикл для списка символов.
        """
        symbols = self.cfg.trading.symbols  # <-- список монет

        self.logger.info("🤖 Orchestrator v9.2 initialized")
        self.logger.info(f"▶️ Starting trading loop for symbols: {symbols}")

        try:
            hb = threading.Thread(target=self._heartbeat_loop, daemon=True)
            hb.start()
            self.loop.run()  # <-- передаём список!
        except Exception as e:
            self.logger.error(f"CRITICAL ERROR in Orchestrator: {e}", exc_info=True)
            err = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            self.bot.send_error(f"CRITICAL FAILURE:\n{err}")
            raise e

    def _heartbeat_loop(self):
        interval_sec = self.cfg.trading.monitoring_interval_minutes * 60
        print(f"[{datetime.now()}] 🚦 Heartbeat LOOP started. Interval={interval_sec} сек.")

        while True:
            try:
                print(f"[{datetime.now()}] ⏳ Сборка heartbeat summary...")
                summary = self.di.build_heartbeat_summary()
                print(f"[{datetime.now()}] ✅ Сформирован heartbeat summary:\n{summary}")

                print(f"[{datetime.now()}] 📤 Отправка heartbeat в Telegram...")
                self.bot.send_heartbeat(summary)
            except Exception as e:
                print(f"[{datetime.now()}] 🛑 Exception в heartbeat loop: {e}")
                try:
                    self.bot.send_message(f"Heartbeat error: {e}")
                except Exception as inner:
                    print(f"[{datetime.now()}] ⚡️ Ошибка при отправке сообщения об ошибке: {inner}")

            print(f"[{datetime.now()}] 💤 Жду {interval_sec} сек до следующего heartbeat...\n")
            time.sleep(interval_sec)
