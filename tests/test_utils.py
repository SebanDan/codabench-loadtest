from urllib.parse import urlparse

import pytest

from codabench_loadtest.clients.utils import rewrite_url_host


@pytest.mark.parametrize(
    "url, host, expected",
    [
        (
            "http://example.com/path?query=1",
            "newhost.com",
            "http://newhost.com/path?query=1",
        ),
        (
            "https://example.com:8080/path?query=1",
            "newhost.com",
            "https://newhost.com:8080/path?query=1",
        ),
        (
            "http://example.com/path#fragment",
            "newhost.com",
            "http://newhost.com/path#fragment",
        ),
        (
            "http://example.com:8080/path?query=1#fragment",
            "newhost.com",
            "http://newhost.com:8080/path?query=1#fragment",
        ),
        (
            "http://example.com:8080/path?query=1#fragment",
            "newhost.com:9090",
            "http://newhost.com:9090/path?query=1#fragment",
        ),
        (
            "http://example.com:8080/path?query=1#fragment",
            "http://newhost.com",
            "http://newhost.com:8080/path?query=1#fragment",
        ),
    ],
)
def test_rewrite_url_host(url, host, expected):
    assert rewrite_url_host(url, host) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://example.com:9000/path",
        "http://10.0.0.1:8080/file?token=abc",
    ],
)
def test_rewrite_url_host_preserves_url_components(url: str) -> None:
    original = urlparse(url)

    rewritten = urlparse(rewrite_url_host(url, "new-host"))

    assert rewritten.scheme == original.scheme
    assert rewritten.port == original.port
    assert rewritten.path == original.path
    assert rewritten.query == original.query
    assert rewritten.fragment == original.fragment
