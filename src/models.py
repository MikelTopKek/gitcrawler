import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchTypeEnum(str, Enum):
    """Supported GitHub search types."""

    REPOSITORIES = "Repositories"
    ISSUES = "Issues"
    WIKIS = "Wikis"


class SearchInput(BaseModel):
    """Input parameters for GitHub search."""

    model_config = ConfigDict(str_strip_whitespace=True)

    keywords: list[str] = Field(min_length=1, description="list of keywords to search for")
    proxies: list[str] = Field(
        min_length=1, description="list of proxy servers (format: host:port or http://host:port)"
    )
    searching_type: SearchTypeEnum

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        """Clean and validate keywords."""
        cleaned = []
        for keyword in v:
            if isinstance(keyword, str):
                keyword = keyword.strip()
                if keyword:
                    cleaned.append(keyword)

        if not cleaned:
            raise ValueError("Keywords are required")

        return cleaned

    @field_validator("proxies")
    @classmethod
    def validate_proxy_format(cls, v: list[str]) -> list[str]:
        """Basic validation of proxy format"""
        validated = []
        for proxy in v:
            proxy = proxy.strip()

            if ":" not in proxy:
                raise ValueError(
                    f"Invalid proxy format: '{proxy}'. " f"Expected format: 'host:port' or 'http://host:port'"
                )

            validated.append(proxy)

        if not validated:
            raise ValueError("At least one valid proxy is required")

        return validated

    def get_search_query(self) -> str:
        """Build search query string from keywords."""
        return " ".join(self.keywords)


class SearchOutput(BaseModel):
    """Output containing search results."""

    model_config = ConfigDict(str_strip_whitespace=True)

    results: list[dict[str, str]] = Field(default_factory=list, description="list of search results with URL")

    def add_result(self, url: str) -> None:
        """Add a single search result."""
        if not url:
            raise ValueError("URL cannot be empty")

        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {url}")

        self.results.append({"url": url})

    def to_json(self) -> str:
        """
        Convert to JSON string matching the required output format.
        Returns a JSON array of objects with 'url' field.
        """

        return json.dumps(self.results, indent=2, ensure_ascii=False)

    @classmethod
    def from_urls(cls, urls: list[str]) -> "SearchOutput":
        """Create SearchOutput from a list of URLs."""
        output = cls()
        for url in urls:
            output.add_result(url)
        return output
