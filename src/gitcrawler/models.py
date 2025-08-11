from typing import Any

from pydantic import BaseModel


class ProxyConfig(BaseModel):
    """Configuration for proxy server"""

    host: str
    port: int
    username: str | None = None
    password: str | None = None

    @property
    def url(self) -> str:
        """Generate proxy URL"""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        else:
            auth = ""
        return f"http://{auth}{self.host}:{self.port}"

    @classmethod
    def from_string(cls, proxy_str: str) -> "ProxyConfig":
        """Create ProxyConfig from string."""
        if "@" in proxy_str:
            auth_part, host_port = proxy_str.split("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
            else:
                username, password = auth_part, None
        else:
            username, password = None, None
            host_port = proxy_str

        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            port = int(port)
        else:
            raise ValueError(f"Invalid proxy format: {proxy_str}")

        return cls(host=host, port=port, username=username, password=password)


class SearchResult(BaseModel):
    """Data class for search results"""

    url: str
    extra: dict[str, Any] | None = None


class RepositoryInfo(BaseModel):
    """Repository information"""

    owner: str
    language_stats: dict[str, float]
