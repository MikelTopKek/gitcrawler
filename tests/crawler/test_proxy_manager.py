from src.gitcrawler.proxy_manager import ProxyManager


def test_get_working_proxy__returns_proxy(proxy_configs) -> None:
    manager = ProxyManager(proxy_configs)

    proxy = manager.get_working_proxy()

    assert proxy is not None
    assert proxy in proxy_configs
    assert manager.proxy_index == 1


def test_mark_proxy_fail(proxy_configs) -> None:
    manager = ProxyManager(proxy_configs)
    proxy = proxy_configs[0]

    manager.mark_proxy_failed(proxy)

    assert proxy.url in manager.failed_proxies


def test_get_working_proxy__skips_failed_proxies(proxy_configs) -> None:
    manager = ProxyManager(proxy_configs)

    manager.mark_proxy_failed(proxy_configs[0])

    proxy = manager.get_working_proxy()
    assert proxy == proxy_configs[1]
