import logging

from src.gitcrawler.models import ProxyConfig

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy rotation"""

    def __init__(self, proxies: list[ProxyConfig]):
        self.proxies = proxies
        self.failed_proxies = set()
        self.proxy_index = 0

    def get_working_proxy(self) -> ProxyConfig | None:
        """Get a working proxy using roundrobin"""
        available_proxies = [p for p in self.proxies if p.url not in self.failed_proxies]

        if not available_proxies:
            logger.warning("All proxies failed, resetting...")
            self.failed_proxies.clear()
            available_proxies = self.proxies

            return None

        proxy = available_proxies[self.proxy_index % len(available_proxies)]
        self.proxy_index += 1
        return proxy

    def mark_proxy_failed(self, proxy: ProxyConfig):
        """Mark proxy as failed"""
        self.failed_proxies.add(proxy.url)
        logger.debug(f"Proxy failed: {proxy.host}:{proxy.port}!")
