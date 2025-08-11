import logging

from src.gitcrawler.crawler import GitHubCrawler
from src.settings import PROXY_LIST, SEARCHING_KEYWORDS, SEARCHING_TYPE

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s ::: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)


async def main():
    """Example usage"""
    config = {
        "keywords": SEARCHING_KEYWORDS,
        "proxies": PROXY_LIST,
        "type": SEARCHING_TYPE,
    }

    crawler = GitHubCrawler()

    try:
        results = await crawler.crawl(config)
        logger.info(f"Found {len(results)} results:")
        for i, result in enumerate(results[:5], 1):
            logger.info(f"{i}. {result.url}")
            if result.extra:
                logger.info(f"Owner: {result.extra.get('owner')}")
                lang_stats = result.extra.get("language_stats", {})
                if lang_stats:
                    logger.info(f"Languages: {dict(list(lang_stats.items())[:3])}")

    except Exception as exc:
        logger.error(f"Error: {exc!r}")
