import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
from src.workers.analytics_worker import consume_url_clicked_events
asyncio.run(consume_url_clicked_events())
