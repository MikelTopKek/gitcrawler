from pytest import fixture
from src.gitcrawler.models import ProxyConfig


@fixture
def proxy_list() -> list[str]:
    return ["192.168.1.1:8080", "10.0.0.1:3128", "proxy.example.com:8888"]


@fixture
def proxy_configs(proxy_list) -> list[ProxyConfig]:
    return [ProxyConfig.from_string(proxy_str) for proxy_str in proxy_list]

