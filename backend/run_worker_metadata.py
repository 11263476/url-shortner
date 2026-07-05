import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
from src.workers.metadata_worker import consume_url_created
asyncio.run(consume_url_created())
