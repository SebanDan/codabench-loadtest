from urllib.parse import urlparse, urlunparse


def rewrite_url_host(url: str, host: str) -> str:
    """Rewrite the host of a given URL to a new host, preserving the original scheme, path, query, and fragment."""
    parsed = urlparse(url)
    new_host = urlparse(
        host if host.startswith(("http://", "https://")) else f"//{host}"
    )
    print(new_host)
    netloc = netloc = (
        new_host.netloc
        if new_host.port
        else f"{new_host.hostname}:{parsed.port}" if parsed.port else new_host.hostname
    )
    print(netloc)
    return urlunparse(parsed._replace(netloc=netloc))
