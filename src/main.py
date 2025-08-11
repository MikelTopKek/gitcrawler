import logging

from src.gitcrawler.crawler import GitHubCrawler
from src.settings import PROXY_LIST

logger = logging.getLogger(__name__)


async def main():
    """Example usage"""
    config = {
        "keywords": ["python", "machine-learning"],
        "proxies": PROXY_LIST,
        "type": "repositories",
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
