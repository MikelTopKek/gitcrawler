import logging

GITHUB_BASE_URL = "https://github.com/"
GITHUB_BASE_URL_SEARCH = GITHUB_BASE_URL + "search"
GITHUB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

PROXY_TIMEOUT = 3
DIRECT_TIMEOUT = 10
MAX_CONCURRENT = 3

SEARCHING_TYPE = "repositories"
SEARCHING_KEYWORDS = ["python", "jwt"]

JSON_SELECTORS = [
    '//script[@data-target="react-app.embeddedData"]/text()',
    '//script[contains(@data-target, "embeddedData")]/text()',
    '//script[contains(text(), "payload")]/text()',
]


PROXY_LIST = [
    "194.4.49.128:10808",
    "116.98.187.72:1022",
    "223.135.156.183:8080",
    "138.197.68.35:4857",
    "38.54.71.67:80",
    "72.10.160.170:3949",
    "123.141.181.85:31",
    "219.65.73.8:180",
    "198.199.86.11:8080",
    "123.30.154.171:7777",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
