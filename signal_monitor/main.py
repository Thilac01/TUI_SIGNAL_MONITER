import queue
import threading
import time
import sys
import os

# Add parent directory to path to find 'scraper' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_monitor.monitor.data.news import NewsFetcher
from signal_monitor.monitor.data.twitter import TwitterMonitor
from signal_monitor.monitor.analysis import Analyzer
from signal_monitor.monitor.tui import TUI

def main():
    # Shared Queues
    log_queue = queue.Queue()
    data_queue = queue.Queue()
    processed_queue = queue.Queue()

    # Initialize Components
    news_fetcher = NewsFetcher(log_queue, data_queue)
    # Default keyword for demo, can be made configurable
    twitter_monitor = TwitterMonitor("Sri Lanka", log_queue, data_queue)
    analyzer = Analyzer()
    tui = TUI(log_queue, processed_queue)

    # Analysis Thread
    def analysis_loop():
        while True:
            try:
                item = data_queue.get(timeout=1)
                processed_item = analyzer.process(item)
                processed_queue.put(processed_item)
            except queue.Empty:
                continue
            except Exception as e:
                log_queue.put({"time": time.time(), "level": "ERROR", "msg": f"Analysis error: {e}"})

    analysis_thread = threading.Thread(target=analysis_loop, daemon=True)
    analysis_thread.start()

    # Start Data Collectors
    news_thread = threading.Thread(target=news_fetcher.run, daemon=True)
    news_thread.start()

    twitter_thread = threading.Thread(target=twitter_monitor.run, daemon=True)
    twitter_thread.start()

    # Start TUI (Main Thread)
    try:
        tui.run()
    except KeyboardInterrupt:
        print("Stopping...")
        news_fetcher.stop()
        twitter_monitor.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
