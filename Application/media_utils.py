def build_absolute_media_url(request, file_field_or_url):
    """
    Safely builds an absolute HTTPS URL for media files in production.
    Prevents Mixed Content warnings on HTTPS client frontends (Vercel, custom domains).
    """
    if not file_field_or_url:
        return None

    url_str = getattr(file_field_or_url, 'url', None) or str(file_field_or_url)
    if not url_str:
        return None

    # If it is already an absolute URL
    if url_str.startswith('http://') or url_str.startswith('https://'):
        if 'server.boatridersports.in' in url_str:
            return url_str.replace('http://', 'https://', 1)
        return url_str

    if not url_str.startswith('/'):
        url_str = f"/{url_str}"

    if request:
        host = request.get_host()
        # In production domain or when secure, always force https
        if 'server.boatridersports.in' in host or request.is_secure():
            scheme = 'https'
        else:
            scheme = request.scheme
        return f"{scheme}://{host}{url_str}"

    return f"https://server.boatridersports.in{url_str}"


def sanitize_https_media(data):
    """
    Recursively replaces http://server.boatridersports.in with https://server.boatridersports.in
    across dicts, lists, and strings (useful for cached responses).
    """
    if isinstance(data, dict):
        return {k: sanitize_https_media(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_https_media(item) for item in data]
    elif isinstance(data, str) and data.startswith("http://server.boatridersports.in"):
        return data.replace("http://server.boatridersports.in", "https://server.boatridersports.in", 1)
    return data
