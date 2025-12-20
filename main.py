# ============================================================
# MAIN v9.2 — Multi-Symbol
# ============================================================
import time
from dependency_container import DependencyContainer
from trading_orchestrator import TradingOrchestrator


def wait_for_first_snapshot(di, timeout=10):
    print("⏳ Waiting for first WS snapshot...")

    start = time.time()
    while (time.time() - start < timeout):
        snap = di.ws_feed.get_prices()
        if snap:
            print(f"✅ First snapshot received: {snap}")
            return True
        time.sleep(0.2)

    print("❌ No WS snapshot received — starting anyway")
    return False


def main():
    print("🚀 AI PRIME TRADING BOT v9.2 starting...")

    di = DependencyContainer()

    wait_for_first_snapshot(di)

    orchestrator = TradingOrchestrator(di.config, di)
    orchestrator.start()


if __name__ == "__main__":
    main()
