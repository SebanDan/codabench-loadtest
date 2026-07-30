from urllib.parse import urlparse, urlunparse


def rewrite_url_host(url: str, host: str) -> str:
    """Rewrite the host of a given URL to a new host, preserving the original scheme, path, query, and fragment."""
    parsed = urlparse(url)
    new_host = urlparse(
        host if host.startswith(("http://", "https://")) else f"//{host}"
    )
    return urlunparse(
        parsed._replace(
            scheme=new_host.scheme or parsed.scheme,
            netloc=new_host.netloc or new_host.hostname,
        )
    )
