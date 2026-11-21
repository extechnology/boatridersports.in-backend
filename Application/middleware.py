class ProxyHttpsFixMiddleware:
    """
    Middleware that ensures Django recognizes HTTPS when running behind
    cPanel / Apache / Passenger / Nginx / Cloudflare reverse proxies.

    When an SSL request arrives at the web server, proxies often terminate SSL
    and forward to Python over plain HTTP. This middleware detects standard SSL
    indicators (X-Forwarded-Proto, X-Forwarded-SSL, HTTPS, CF-Visitor, or production host)
    and populates HTTP_X_FORWARDED_PROTO and wsgi.url_scheme so Django's request.is_secure()
    and request.scheme accurately return 'https'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        is_prod_host = host in ['server.boatridersports.in', 'boatridersports.in']

        x_proto = request.META.get('HTTP_X_FORWARDED_PROTO', '').lower()
        x_ssl = request.META.get('HTTP_X_FORWARDED_SSL', '').lower()
        https_env = request.META.get('HTTPS', '').lower()
        cf_visitor = request.META.get('HTTP_CF_VISITOR', '')

        is_secure = (
            is_prod_host or
            'https' in x_proto or
            x_ssl in ['on', '1'] or
            https_env in ['on', '1'] or
            '"scheme":"https"' in cf_visitor or
            request.META.get('SERVER_PORT') == '443'
        )

        if is_secure:
            request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
            request.META['wsgi.url_scheme'] = 'https'

        return self.get_response(request)
