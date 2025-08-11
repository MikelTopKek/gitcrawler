import csv
from http import HTTPStatus
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.gitcrawler.crawler import GitHubCrawler
from src.gitcrawler.models import ProxyConfig, RepositoryInfo, SearchResult


def test_crawler_init__no_proxies(temp_dir):
    crawler = GitHubCrawler(output_dir=temp_dir)

    assert crawler.proxy_manager is None
    assert crawler.output_dir == Path(temp_dir)
    assert crawler.session is None


def test_crawler_init_with_proxies__ok(proxy_list, temp_dir):
    valid_proxies = []
    for proxy_str in proxy_list:
        try:
            ProxyConfig.from_string(proxy_str)
            valid_proxies.append(proxy_str)
        except ValueError:
            pass

    crawler = GitHubCrawler(proxies=proxy_list, output_dir=temp_dir)

    assert crawler.proxy_manager is not None
    assert len(crawler.proxy_manager.proxies) == len(valid_proxies)


def test_crawler_init_invalid_proxy__fail(temp_dir):
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        crawler = GitHubCrawler(proxies=["invalid_proxy"], output_dir=temp_dir)

        assert crawler.proxy_manager is None


def test_build_search_url__repositories__ok():
    crawler = GitHubCrawler()

    url = crawler._build_search_url(["python", "web"], "repositories")

    assert "python+web" in url
    assert "type=repositories" in url
    assert url.startswith("https://github.com/search")


def test_build_search_url__issues():
    crawler = GitHubCrawler()

    url = crawler._build_search_url(["bug", "fix"], "issues")

    assert "bug+fix" in url
    assert "type=issues" in url


def test_extract_urls_from_json__repositories(sample_json_data):
    crawler = GitHubCrawler()

    urls = crawler._extract_urls_from_json(sample_json_data, "repositories")

    assert len(urls) == 2
    assert "https://github.com/user/some_repoo" in urls
    assert "https://github.com/user128001/repo2" in urls


def test_extract_urls_from_json__issues(sample_json_data):
    crawler = GitHubCrawler()

    urls = crawler._extract_urls_from_json(sample_json_data, "issues")

    assert len(urls) == 2
    assert "https://github.com/user/some_repoo/issues/322" in urls
    assert "https://github.com/user128001/repo2/issues/1123" in urls


def test_extract_urls_from_json__wikis__ok(sample_json_data):
    crawler = GitHubCrawler()

    urls = crawler._extract_urls_from_json(sample_json_data, "wikis")

    assert len(urls) == 1  # Only first result has path, second uses title
    assert "https://github.com/user/some_repoo/wiki/path" in urls


def test_extract_urls_from_json__empty_payload():
    crawler = GitHubCrawler()
    empty_data = {"payload": {"results": []}}

    urls = crawler._extract_urls_from_json(empty_data, "repositories")

    assert len(urls) == 0


def test_extract_urls_from_json__missing_data():
    crawler = GitHubCrawler()
    invalid_data = {
        "payload": {
            "results": [{"repo": {"repository": {"owner_login": "user"}}}, {"repo": {"repository": {"name": "repo"}}}]
        }
    }

    urls = crawler._extract_urls_from_json(invalid_data, "repositories")

    assert len(urls) == 0


def test_save_to_csv__repositories(search_results, temp_dir):
    crawler = GitHubCrawler(output_dir=temp_dir)

    crawler._save_to_csv(search_results, "repositories", ["python"])

    csv_files = list(Path(temp_dir).glob("repositories_python_*.csv"))
    assert len(csv_files) == 1

    with open(csv_files[0], "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["url"] == "https://github.com/user1/repo1"
        if rows[1].get("owner"):
            assert rows[1]["owner"] == "user2"


def test_save_to_csv__simple_results(temp_dir, test_url_github_repo):
    crawler = GitHubCrawler(output_dir=temp_dir)
    simple_results = [SearchResult(url=test_url_github_repo)]

    crawler._save_to_csv(simple_results, "issues", ["bug"])

    csv_files = list(Path(temp_dir).glob("issues_bug_*.csv"))
    assert len(csv_files) == 1

    with open(csv_files[0], "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["url"] == test_url_github_repo


@pytest.mark.asyncio
async def test_search__no_html_content():
    crawler = GitHubCrawler()

    with patch.object(crawler, "_fetch_page", return_value=None):
        results = await crawler.search(["python"], "repositories")

        assert len(results) == 0


@pytest.mark.asyncio
async def test_search__basic_repositories(test_url_github_repo):
    crawler = GitHubCrawler()
    mock_html = "<html>test</html>"
    mock_urls = [test_url_github_repo + "1", test_url_github_repo + "2"]

    mock_session = AsyncMock()

    with patch.object(crawler, "_fetch_page", return_value=mock_html), patch.object(
        crawler, "_parse_search_results", return_value=mock_urls
    ), patch.object(crawler, "_create_session", return_value=mock_session):
        results = await crawler.search(["python"], "repositories", extract_extra=False)

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].url == mock_urls[0]


@pytest.mark.asyncio
async def test_crawler__ok(temp_dir, test_url):
    config = {"keywords": ["python"], "proxies": [], "type": "repositories"}

    crawler = GitHubCrawler(output_dir=temp_dir)
    mock_results = [SearchResult(url=test_url)]

    with patch.object(crawler, "search", return_value=mock_results), patch.object(crawler, "_save_to_csv"):
        results = await crawler.crawl(config)

        assert len(results) == 1
        assert results[0].url == test_url


@pytest.mark.asyncio
async def test_crawl__empty_keywords():
    config = {"keywords": [], "type": "repositories"}
    crawler = GitHubCrawler()

    with pytest.raises(ValueError, match="Keywords list cannot be empty"):
        await crawler.crawl(config)


@pytest.mark.asyncio
async def test_crawl__with_proxies(temp_dir, test_ip):
    config = {"keywords": ["python"], "proxies": [test_ip], "type": "repositories"}

    crawler = GitHubCrawler(output_dir=temp_dir)

    with patch.object(crawler, "search", return_value=[]), patch.object(crawler, "_save_to_csv"):
        await crawler.crawl(config)

        assert crawler.proxy_manager is not None
        assert len(crawler.proxy_manager.proxies) == 1


@pytest.mark.asyncio
async def test_fetch_direct__success(test_url):
    crawler = GitHubCrawler()

    mock_response = MagicMock()
    mock_response.status = HTTPStatus.OK
    mock_response.text = AsyncMock(return_value="test content")

    mock_session = MagicMock()
    mock_session.get.return_value = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response

    crawler.session = mock_session

    result = await crawler._fetch_direct(test_url)

    assert result == "test content"


@pytest.mark.asyncio
async def test_fetch_direct__failure(test_url):
    crawler = GitHubCrawler()
    crawler.session = AsyncMock()

    mock_response = AsyncMock()
    mock_response.status = HTTPStatus.NOT_FOUND
    crawler.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)

    result = await crawler._fetch_direct(test_url)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_with_proxy__success(test_url, test_ip):
    crawler = GitHubCrawler()
    proxy = ProxyConfig.from_string(test_ip)

    mock_response = MagicMock()
    mock_response.status = HTTPStatus.OK
    mock_response.text = AsyncMock(return_value="proxy content")

    mock_session = MagicMock()
    mock_session.get.return_value = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response

    crawler.session = mock_session

    content, success = await crawler._fetch_with_proxy(test_url, proxy)

    assert content == "proxy content"
    assert success is True


@pytest.mark.asyncio
async def test_fetch_with_proxy__failure(test_url, test_ip):
    crawler = GitHubCrawler()
    crawler.session = AsyncMock()
    proxy = ProxyConfig.from_string(test_ip)

    mock_response = AsyncMock()
    mock_response.status = HTTPStatus.FORBIDDEN
    crawler.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)

    content, success = await crawler._fetch_with_proxy(test_url, proxy)

    assert content is None
    assert success is False


@pytest.mark.asyncio
async def test_fetch_with_proxy__exception(test_url, test_ip):
    crawler = GitHubCrawler()
    crawler.session = AsyncMock()
    proxy = ProxyConfig.from_string(test_ip)
    crawler.session.get.side_effect = Exception("Proxy error")

    content, success = await crawler._fetch_with_proxy(test_url, proxy)

    assert content is None
    assert success is False


@pytest.mark.asyncio
async def test_extract_repository_info__success(language_stats, test_url_github_repo):
    crawler = GitHubCrawler()
    mock_html = f"""
    <html>
        <span class="color-fg-default text-bold mr-1">Python</span>
        <span>{language_stats}%</span>
        <span class="color-fg-default text-bold mr-1">JavaScript</span>
        <span>14.5%</span>
    </html>
    """

    with patch.object(crawler, "_fetch_page", return_value=mock_html):
        result = await crawler._extract_repository_info(test_url_github_repo)

        assert result is not None
        assert result.owner == "user"
        assert "Python" in result.language_stats
        assert result.language_stats["Python"] == language_stats


@pytest.mark.asyncio
async def test_extract_repository_info__no_content(test_url_github_repo):
    crawler = GitHubCrawler()

    with patch.object(crawler, "_fetch_page", return_value=None):
        result = await crawler._extract_repository_info(test_url_github_repo)

        assert result is None


@pytest.mark.asyncio
async def test_extract_repository_info__exception(test_url_github_repo):
    crawler = GitHubCrawler()

    with patch.object(crawler, "_fetch_page", side_effect=Exception("Parse error")):
        result = await crawler._extract_repository_info(test_url_github_repo)

        assert result is None


def test_parse_search_results__no_json():
    crawler = GitHubCrawler()
    mock_html = "<html>no json here</html>"

    with patch("lxml.html.fromstring") as mock_fromstring:
        mock_tree = MagicMock()
        mock_tree.xpath.return_value = []
        mock_fromstring.return_value = mock_tree

        urls = crawler._parse_search_results(mock_html, "repositories")

        assert len(urls) == 0


def test_parse_search_results__exception():
    crawler = GitHubCrawler()

    with patch("lxml.html.fromstring", side_effect=Exception("Parse error")):
        urls = crawler._parse_search_results("<html></html>", "repositories")

        assert len(urls) == 0


@pytest.mark.asyncio
async def test_search__with_repository_extraction(test_url_github_repo):
    crawler = GitHubCrawler()
    mock_html = "<html>test</html>"
    mock_urls = [test_url_github_repo]

    with patch.object(crawler, "_fetch_page", return_value=mock_html), patch.object(
        crawler, "_parse_search_results", return_value=mock_urls
    ), patch.object(crawler, "_create_session", return_value=AsyncMock()), patch.object(
        crawler, "_extract_repository_info", return_value=None
    ):
        results = await crawler.search(["python"], "repositories", extract_extra=True)

        assert len(results) == len(mock_urls)
        assert results[0].extra is None


@pytest.mark.asyncio
async def test_search__repositories_with_extra_extraction(test_url_github_repo):
    crawler = GitHubCrawler()
    mock_html = "<html>test</html>"
    mock_urls = [test_url_github_repo + "1", test_url_github_repo + "2"]

    mock_session = AsyncMock()

    async def mock_extract_repo_info(url):
        if "repo1" in url:
            return RepositoryInfo(owner="user", language_stats={"Python": 80.0})
        return None

    with patch.object(crawler, "_fetch_page", return_value=mock_html), patch.object(
        crawler, "_parse_search_results", return_value=mock_urls
    ), patch.object(crawler, "_create_session", return_value=mock_session), patch.object(
        crawler, "_extract_repository_info", side_effect=mock_extract_repo_info
    ):
        results = await crawler.search(["python"], "repositories", extract_extra=True)

        assert len(results) == len(mock_urls)
        assert results[0].extra is not None
        assert results[0].extra["owner"] == "user"
        assert results[1].extra is None
