import feedparser
import time
import threading
from datetime import datetime

class NewsFetcher:
    def __init__(self, log_queue, data_queue, interval=300):
        self.log_queue = log_queue
        self.data_queue = data_queue
        self.interval = interval
        self.stopped = False
        self.sources = {
            "Ada Derana": "http://www.adaderana.lk/rss.php",
            "Daily Mirror": "https://www.dailymirror.lk/RSS_Feeds/breaking-news",
            "Lanka C News": "https://lankacnews.com/feed/",
            "Colombo Page": "http://www.colombopage.com/feed.xml"
        }
        self.seen_links = set()

    def log(self, level, msg):
        payload = {"time": time.time(), "level": level, "msg": msg, "source": "NewsFetcher"}
        try:
            self.log_queue.put(payload, block=False)
        except:
            pass

    def fetch_feeds(self):
        self.log("INFO", "Starting News Fetcher cycle...")
        for name, url in self.sources.items():
            if self.stopped: break
            try:
                self.log("DEBUG", f"Fetching {name}...")
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    link = entry.get("link", "")
                    if link and link not in self.seen_links:
                        self.seen_links.add(link)
                        
                        # Extract relevant fields
                        title = entry.get("title", "No Title")
                        summary = entry.get("summary", "")
                        published = entry.get("published", str(datetime.now()))
                        
                        item = {
                            "type": "news",
                            "source": name,
                            "title": title,
                            "text": summary,
                            "url": link,
                            "timestamp": published
                        }
                        self.data_queue.put(item)
                        self.log("NEWS", f"[{name}] {title}")
            except Exception as e:
                self.log("ERROR", f"Failed to fetch {name}: {e}")

    def run(self):
        self.log("INFO", "NewsFetcher started.")
        while not self.stopped:
            self.fetch_feeds()
            for _ in range(self.interval):
                if self.stopped: break
                time.sleep(1)
        self.log("INFO", "NewsFetcher stopped.")

    def stop(self):
        self.stopped = True
