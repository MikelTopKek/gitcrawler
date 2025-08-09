from pytest import fixture


@fixture
def search_input_keywords() -> list[str]:
    return ["input_keyword1", "input_keyword2"]


@fixture
def search_info_proxies() -> list[str]:
    return ["192.168.1.1:8000", "11.1.1.1:1111"]


@fixture
def search_info_proxies_invalid() -> list[str]:
    return ["192.168.1.1:8000", "11.1.1.1:1111", "11.1.1.1"]
