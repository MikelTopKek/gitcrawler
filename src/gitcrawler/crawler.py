import asyncio
import csv
import json
import logging
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import quote

import aiohttp
from lxml import html

from src.gitcrawler.models import ProxyConfig, RepositoryInfo, SearchResult
from src.gitcrawler.proxy_manager import ProxyManager
from src.settings import (
    DIRECT_TIMEOUT,
    GITHUB_BASE_URL,
    GITHUB_BASE_URL_SEARCH,
    GITHUB_HEADERS,
    JSON_SELECTORS,
    MAX_CONCURRENT,
    PROXY_LIST,
    PROXY_TIMEOUT,
)

logger = logging.getLogger(__name__)


class GitHubCrawler:
    """
    GitHub crawler implementation.
    Supports "repositories", "issues", and "wikis" search with proxy rotation
    """

    SUPPORTED_TYPES = (
        "repositories",
        "issues",
        "wikis",
    )

    def __init__(self, proxies: list[str] | None = None, output_dir: str = "results") -> None:
        self.session = None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        if proxies:
            proxy_configs = []
            for proxy_str in proxies:
                try:
                    proxy_configs.append(ProxyConfig.from_string(proxy_str))
                except ValueError as exc:
                    logger.error(f"Invalid proxy: {proxy_str} : {exc!r}")
            self.proxy_manager = ProxyManager(proxy_configs) if proxy_configs else None
        else:
            self.proxy_manager = None

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session"""
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        return aiohttp.ClientSession(headers=GITHUB_HEADERS, connector=connector)

    async def _fetch_with_proxy(self, url: str, proxy: ProxyConfig) -> tuple[str | None, bool]:
        """Fetch page using proxy"""
        try:
            timeout = aiohttp.ClientTimeout(total=PROXY_TIMEOUT)
            async with self.session.get(url, proxy=proxy.url, timeout=timeout, ssl=False) as response:
                if response.status == HTTPStatus.OK:
                    return await response.text(), True
                return None, False
        except Exception:
            return None, False

    async def _fetch_direct(self, url: str) -> str | None:
        """Fetch page without proxy"""
        try:
            timeout = aiohttp.ClientTimeout(total=DIRECT_TIMEOUT)
            async with self.session.get(url, timeout=timeout) as response:
                if response.status == HTTPStatus.OK:
                    return await response.text()
        except Exception:
            pass
        return None

    async def _fetch_page(self, url: str) -> str | None:
        """Fetch page with proxy rotation"""
        if self.proxy_manager:
            proxies_to_try = []
            for _ in range(min(MAX_CONCURRENT, len(self.proxy_manager.proxies))):
                proxy = self.proxy_manager.get_working_proxy()
                if proxy and proxy not in proxies_to_try:
                    proxies_to_try.append(proxy)

            if proxies_to_try:

                async def try_proxy(proxy):
                    content, success = await self._fetch_with_proxy(url, proxy)
                    if not success:
                        self.proxy_manager.mark_proxy_failed(proxy)
                    return content if success else None

                tasks = [asyncio.create_task(try_proxy(proxy)) for proxy in proxies_to_try]

                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    if result:
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        return result

        return await self._fetch_direct(url)

    async def _extract_repository_info(self, repo_url: str) -> RepositoryInfo | None:
        """Extract repository owner and language stats"""
        try:
            html_content = await self._fetch_page(repo_url)
            if not html_content:
                return None

            tree = html.fromstring(html_content)

            owner = repo_url.replace(GITHUB_BASE_URL, "").split("/")[0]

            language_stats = {}

            lang_elements = tree.xpath('//span[@class="color-fg-default text-bold mr-1"]/text()')
            percent_elements = tree.xpath('//span[contains(text(), "%")]/text()')

            for lang, percent in zip(lang_elements, percent_elements):
                try:
                    percent_val = float(percent.replace("%", "").strip())
                    language_stats[lang.strip()] = percent_val
                except (ValueError, AttributeError):
                    continue

            return RepositoryInfo(owner=owner, language_stats=language_stats)

        except Exception as exc:
            logger.debug(f"Error extracting repository info: {exc!r}")
            return None

    def _extract_urls_from_json(self, json_data: dict, search_type: str) -> list[str]:
        """Extract URLs from GitHub search JSON data"""
        urls = []
        results = json_data.get("payload", {}).get("results", [])

        for result in results:
            repo = result.get("repo", {}).get("repository", {})
            owner = repo.get("owner_login")
            repo_name = repo.get("name")

            if not owner or not repo_name:
                continue

            try:
                match search_type:
                    case "repositories":
                        url = f"{GITHUB_BASE_URL}{owner}/{repo_name}"
                    case "issues":
                        if number := result.get("number"):
                            url = f"{GITHUB_BASE_URL}{owner}/{repo_name}/issues/{number}"
                        else:
                            continue
                    case "wikis":
                        if path := result.get("path") or result.get("title"):
                            path = quote(path, safe="")
                            url = f"{GITHUB_BASE_URL}{owner}/{repo_name}/wiki/{path}"
                        else:
                            continue
                    case _:
                        continue

                urls.append(url)
            except Exception:
                continue

        return urls

    def _parse_search_results(self, html_content: str, search_type: str) -> list[str]:
        """Parse GitHub search results HTML and extract URLs"""
        try:
            tree = html.fromstring(html_content)

            for selector in JSON_SELECTORS:
                script_elements = tree.xpath(selector)
                if script_elements:
                    json_data = json.loads(script_elements[0])
                    urls = self._extract_urls_from_json(json_data, search_type)
                    logger.info(f"Extracted {len(urls)} URLS")
                    return urls

            logger.warning("No JSON data found")
            return []

        except Exception as exc:
            logger.error(f"Parsing error: {exc!r}")
            return []

    def _build_search_url(self, keywords: list[str], search_type: str) -> str:
        """Build GitHub search URL"""
        query = "+".join(quote(keyword, safe="") for keyword in keywords)
        return f"{GITHUB_BASE_URL_SEARCH}?q={query}&type={search_type}"

    def _save_to_csv(self, results: list[SearchResult], search_type: str, keywords: list[str]):
        """Save search results to CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keywords_str = "_".join(keywords[:3])
        filename = f"{search_type}_{keywords_str}_{timestamp}.csv"
        filepath = self.output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            if search_type == "repositories" and results and results[0].extra:
                fieldnames = ["url", "owner", "language_stats"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for result in results:
                    row = {"url": result.url}
                    if result.extra:
                        row.update(
                            {
                                "owner": result.extra.get("owner", ""),
                                "language_stats": json.dumps(result.extra.get("language_stats", {})),
                            }
                        )
                    writer.writerow(row)
            else:
                fieldnames = ["url"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for result in results:
                    writer.writerow({"url": result.url})

        logger.info(f"Saved {len(results)} results to {filepath}")

    async def search(self, keywords: list[str], search_type: str, extract_extra: bool = True) -> list[SearchResult]:
        """Perform GitHub search and extracting URLs"""
        if search_type.lower() not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported search type: {search_type}")

        search_url = self._build_search_url(keywords, search_type.lower())
        logger.info(f"Searching: {search_url}")

        self.session = await self._create_session()
        try:
            html_content = await self._fetch_page(search_url)
            if not html_content:
                return []

            urls = self._parse_search_results(html_content, search_type.lower())
            results = []

            if search_type.lower() == "repositories" and extract_extra and urls:
                logger.info(f"Extracting repository info for {len(urls)} repositories...")

                semaphore = asyncio.Semaphore(MAX_CONCURRENT)

                async def process_repo(url):
                    async with semaphore:
                        repo_info = await self._extract_repository_info(url)
                        result = SearchResult(url=url)
                        if repo_info:
                            result.extra = repo_info.model_dump()
                        return result

                tasks = [process_repo(url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                results = [r for r in results if not isinstance(r, Exception)]
            else:
                results = [SearchResult(url=url) for url in urls]

            return results

        finally:
            await self.session.close()

    async def crawl(self, config: dict[str, Any]) -> list[SearchResult]:
        """Perform crawling according to configs"""
        keywords = config.get("keywords", [])
        proxies = PROXY_LIST
        search_type = config.get("type", "repositories")

        if not keywords:
            raise ValueError("Keywords list cannot be empty")

        if proxies:
            proxy_configs = []
            for proxy_str in proxies:
                try:
                    proxy_configs.append(ProxyConfig.from_string(proxy_str))
                except ValueError as exc:
                    logger.error(f"Invalid proxy: {proxy_str} error: {exc!r}")
            self.proxy_manager = ProxyManager(proxy_configs) if proxy_configs else None

        results = await self.search(keywords, search_type, extract_extra=True)

        self._save_to_csv(results, search_type, keywords)

        return results
