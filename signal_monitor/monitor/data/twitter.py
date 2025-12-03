import threading
import time
import queue
import sys
import os

# Ensure we can find 'scraper' if running from here or main
try:
    from scraper.scraper import TweetScraper
except ImportError:
    # Fallback if path not set
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from scraper.scraper import TweetScraper

class TwitterMonitor:
    def __init__(self, keyword, log_queue, data_queue, max_tweets=100):
        self.keyword = keyword
        self.log_queue = log_queue
        self.data_queue = data_queue
        self.max_tweets = max_tweets
        self.tweets_list = [] # Local buffer for the scraper
        self.scraper = None
        self.thread = None
        self.stopped = False
        self.last_processed_index = 0

    def log(self, level, msg):
        # Adapt scraper logs to our format if needed, or just pass through
        # But here we are logging from the Monitor wrapper
        payload = {"time": time.time(), "level": level, "msg": msg, "source": "TwitterMonitor"}
        try:
            self.log_queue.put(payload, block=False)
        except:
            pass

    def _scraper_log_adapter(self):
        # The scraper writes to its own log_queue. We need to bridge that to our main log_queue
        # However, the scraper expects a queue instance. We can pass the SAME queue if formats match.
        # The scraper uses: {"time": ..., "level": ..., "msg": ...}
        # We use: {"time": ..., "level": ..., "msg": ..., "source": ...}
        # It's better to wrap it or just let it be. 
        # For simplicity, we will pass the main log_queue to the scraper, 
        # but the scraper doesn't add "source". We can handle that in the TUI display.
        pass

    def run(self):
        self.log("INFO", f"Starting Twitter Monitor for '{self.keyword}'...")
        
        # Initialize the existing TweetScraper
        # We pass self.log_queue directly. The scraper will push logs there.
        # We pass self.tweets_list. The scraper will append tweets there.
        settings = {
            "headless": True,
            "scroll_delay": 2,
            "max_consecutive_scrolls": 20
        }
        
        self.scraper = TweetScraper(
            keyword=self.keyword, 
            max_tweets=self.max_tweets, 
            settings=settings, 
            log_queue=self.log_queue, 
            tweets_list=self.tweets_list
        )
        
        # Start scraper in a separate thread
        self.thread = threading.Thread(target=self.scraper.run, daemon=True)
        self.thread.start()
        
        # Monitor the tweets_list and push new items to data_queue
        while not self.stopped:
            current_len = len(self.tweets_list)
            if current_len > self.last_processed_index:
                new_tweets = self.tweets_list[self.last_processed_index:current_len]
                for tweet in new_tweets:
                    item = {
                        "type": "social",
                        "source": "Twitter",
                        "user": tweet.get("username", "Unknown"),
                        "handle": tweet.get("handle", ""),
                        "text": tweet.get("text", ""),
                        "url": tweet.get("url", ""),
                        "timestamp": tweet.get("timestamp", "")
                    }
                    self.data_queue.put(item)
                self.last_processed_index = current_len
            
            if not self.thread.is_alive():
                self.log("WARN", "Scraper thread finished.")
                break
                
            time.sleep(1)

    def stop(self):
        self.stopped = True
        if self.scraper:
            self.scraper.stop()
        if self.thread:
            self.thread.join(timeout=5)
