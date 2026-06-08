import asyncio, signal

from src.logging import setup_logging, get_logger
from src.core.database import AsyncSessionLocal
from src.repositories import URLRepository, AnalyticsRepository
from src.documents.click_event import ClickEvent


async def run_aggregation_rollup(logger):
    pipeline = [
        {"$group": {
            "_id": "$short_code",
            "unique_ips": {"$addToSet": "$ip_address"},
            "total_clicks": {"$sum": 1},
        }},
        {"$project": {
            "short_code": "$_id",
            "unique_clicks": {"$size": "$unique_ips"},
            "total_clicks": "$total_clicks",
        }},
    ]

    try:
        mongo_results = await ClickEvent.aggregate(pipeline).to_list()
    except Exception as e:
        logger.error("Failed to aggregate MongoDB events: %s", str(e))
        return

    if not mongo_results:
        return

    async with AsyncSessionLocal() as db:
        url_repo = URLRepository(db)
        analytics_repo = AnalyticsRepository(db)
        updated_count = 0

        for item in mongo_results:
            short_code = item["short_code"]
            url_id = await url_repo.get_url_id_by_short_code(short_code)
            if not url_id:
                continue
            await analytics_repo.upsert_rollup(url_id, item["total_clicks"], item["unique_clicks"])
            updated_count += 1

        logger.info("Rolled up %d analytics summaries.", updated_count)


async def start_worker():
    setup_logging()
    logger = get_logger("aggregation-worker")
    logger.info("Aggregation Worker started")
    interval = 60
    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    while not stop.is_set():
        try:
            await run_aggregation_rollup(logger)
        except Exception as e:
            logger.warning("Error in aggregation loop: %s", str(e))
        await asyncio.sleep(interval)

    logger.info("Aggregation Worker stopped")


if __name__ == "__main__":
    asyncio.run(start_worker())
