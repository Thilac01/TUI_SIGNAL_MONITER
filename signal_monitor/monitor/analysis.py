from textblob import TextBlob

class Analyzer:
    def __init__(self):
        self.risk_keywords = ["strike", "protest", "shortage", "inflation", "crisis", "danger", "warning", "riot", "curfew"]
        self.opportunity_keywords = ["growth", "investment", "development", "opening", "launch", "success", "profit", "recovery"]

    def analyze_sentiment(self, text):
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except:
            return 0.0

    def extract_signals(self, text):
        text_lower = text.lower()
        signals = []
        
        for kw in self.risk_keywords:
            if kw in text_lower:
                signals.append(f"RISK: {kw.upper()}")
                
        for kw in self.opportunity_keywords:
            if kw in text_lower:
                signals.append(f"OPP: {kw.upper()}")
                
        return signals

    def categorize(self, text):
        # Simple heuristic categorization
        text_lower = text.lower()
        if any(x in text_lower for x in ["strike", "protest", "riot"]):
            return "Operational Environment"
        elif any(x in text_lower for x in ["inflation", "economy", "price", "market"]):
            return "National Activity"
        else:
            return "General"

    def process(self, item):
        text = item.get("text", "")
        sentiment = self.analyze_sentiment(text)
        signals = self.extract_signals(text)
        category = self.categorize(text)
        
        item["sentiment"] = sentiment
        item["signals"] = signals
        item["category"] = category
        
        return item
