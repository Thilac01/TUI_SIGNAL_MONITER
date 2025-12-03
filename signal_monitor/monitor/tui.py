from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich import box
import queue
import time
from datetime import datetime

class TUI:
    def __init__(self, log_queue, data_queue):
        self.log_queue = log_queue
        self.data_queue = data_queue
        self.console = Console()
        self.layout = Layout()
        self.items = []
        self.logs = []
        self.stats = {
            "News": 0,
            "Social": 0,
            "Risks": 0,
            "Opportunities": 0
        }

    def make_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="feed", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        self.layout["sidebar"].split_column(
            Layout(name="stats", size=10),
            Layout(name="logs")
        )
        return self.layout

    def update_header(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            "[b cyan]Sri Lanka Socio-Economic Signal Monitor[/b cyan]",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        return Panel(grid, style="white on blue")

    def update_feed(self):
        table = Table(expand=True, box=box.SIMPLE_HEAD)
        table.add_column("Time", style="dim", width=12)
        table.add_column("Source", width=15)
        table.add_column("Category", width=15)
        table.add_column("Content")
        table.add_column("Sentiment", justify="right", width=10)

        # Show last 15 items
        for item in self.items[-15:]:
            sentiment_color = "green" if item.get("sentiment", 0) > 0.1 else "red" if item.get("sentiment", 0) < -0.1 else "white"
            
            content = item.get("text", "")[:100].replace("\n", " ")
            if item.get("signals"):
                content += f"\n[bold yellow]{' '.join(item['signals'])}[/bold yellow]"
                
            table.add_row(
                item.get("timestamp", "")[:19],
                f"[{item.get('source', 'Unknown')}]",
                item.get("category", "General"),
                content,
                f"[{sentiment_color}]{item.get('sentiment', 0):.2f}[/{sentiment_color}]"
            )
        return Panel(table, title="Live Signal Feed", border_style="green")

    def update_stats(self):
        table = Table(expand=True, box=None)
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        
        table.add_row("News Items", str(self.stats["News"]))
        table.add_row("Social Posts", str(self.stats["Social"]))
        table.add_row("Risk Signals", f"[red]{self.stats['Risks']}[/red]")
        table.add_row("Opp Signals", f"[green]{self.stats['Opportunities']}[/green]")
        
        return Panel(table, title="Statistics", border_style="yellow")

    def update_logs(self):
        text = Text()
        for log in self.logs[-10:]:
            level_color = "green" if log["level"] == "INFO" else "yellow" if log["level"] == "WARN" else "red"
            text.append(f"[{log['time']:.0f}] [{level_color}]{log['level']}[/{level_color}] {log['msg']}\n")
        return Panel(text, title="System Logs", border_style="white")

    def run(self):
        self.make_layout()
        with Live(self.layout, refresh_per_second=4, screen=True) as live:
            while True:
                # Process Data Queue
                while not self.data_queue.empty():
                    try:
                        item = self.data_queue.get_nowait()
                        self.items.append(item)
                        
                        # Update stats
                        if item.get("type") == "news": self.stats["News"] += 1
                        elif item.get("type") == "social": self.stats["Social"] += 1
                        
                        signals = item.get("signals", [])
                        for s in signals:
                            if "RISK" in s: self.stats["Risks"] += 1
                            if "OPP" in s: self.stats["Opportunities"] += 1
                    except: pass

                # Process Log Queue
                while not self.log_queue.empty():
                    try:
                        log = self.log_queue.get_nowait()
                        self.logs.append(log)
                    except: pass

                # Update Layout
                self.layout["header"].update(self.update_header())
                self.layout["feed"].update(self.update_feed())
                self.layout["stats"].update(self.update_stats())
                self.layout["logs"].update(self.update_logs())
                self.layout["footer"].update(Panel("Press Ctrl+C to exit", style="dim"))
                
                time.sleep(0.1)
