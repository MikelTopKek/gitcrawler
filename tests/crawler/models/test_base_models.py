import pytest
from pydantic import ValidationError
from src.models import SearchInput, SearchTypeEnum


def test_valid_input_creation__ok(search_input_keywords, search_info_proxies) -> None:
    input_data = SearchInput(
        keywords=search_input_keywords, proxies=search_info_proxies, searching_type=SearchTypeEnum.REPOSITORIES
    )

    assert input_data.keywords == search_input_keywords
    assert len(input_data.proxies) == len(search_info_proxies)
    assert input_data.searching_type == SearchTypeEnum.REPOSITORIES


def test_keyword_validation__ok(search_input_keywords, search_info_proxies) -> None:
    input_data = SearchInput(
        keywords=[f"  {k} " for k in search_input_keywords],
        proxies=search_info_proxies,
        searching_type=SearchTypeEnum.REPOSITORIES,
    )
    assert input_data.keywords == search_input_keywords


def test_empty_keywords_validation__fail(search_info_proxies) -> None:
    with pytest.raises(ValidationError) as exc_info:
        SearchInput(keywords=[], proxies=search_info_proxies, searching_type=SearchTypeEnum.REPOSITORIES)
    assert "at least 1 item" in str(exc_info.value).lower()


def test_proxy_validation__ok(search_input_keywords, search_info_proxies) -> None:
    input_data = SearchInput(
        keywords=search_input_keywords, proxies=search_info_proxies, searching_type=SearchTypeEnum.REPOSITORIES
    )
    assert len(input_data.proxies) == len(search_info_proxies)


def test_proxy_validation__fail(search_input_keywords, search_info_proxies_invalid) -> None:
    with pytest.raises(ValidationError) as exc_info:
        SearchInput(
            keywords=search_input_keywords,
            proxies=search_info_proxies_invalid,
            searching_type=SearchTypeEnum.REPOSITORIES,
        )
    assert "invalid proxy format" in str(exc_info.value).lower()
