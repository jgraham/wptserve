"""Compatibility layer between wptserve and mozhttpd"""
import json

import server
import handlers as wpthandlers

class MozHttpdRequest(object):
    def __init__(self, request):
        self.uri = request.url
        self.headers = request._raw_headers
        for key, value in request.url_parts._asdict().iteritems():
            setattr(self, key, value)
        self.body = request.body

class MozHttpdHandler(object):
    def __init__(self, handler):
        self.handler = handler

    def __call__(self, request, response):
        status_code, headers, data = self.handler(MozHttpdRequest(request), *request.route_match.groups())
        response.status = status_code
        response.headers.update((name, value) for name, value in headers.iteritems())
        response.content = data

        return response

class Handlers(object):
    def json_response(self, func):
        """ Translates results of 'func' into a JSON response. """
        def wrap(*a, **kw):
            (code, data) = func(*a, **kw)
            json_data = json.dumps(data)
            return (code, { 'Content-type': 'application/json',
                            'Content-Length': len(json_data) }, json_data)

        return wrap
handlers = Handlers()

def urlhandlers_to_routes(urlhandlers):
    rv = []
    for handler in urlhandlers:
        method = handler["method"]
        path = handler["path"]
        func = handler["function"]
        if method == "DEL":
            method = "DELETE"
        rv.append((method, path, MozHttpdHandler(func)))
    return rv

def MozHttpd(host="127.0.0.1", port=0, docroot=None,
             urlhandlers=None, proxy_host_dirs=False, log_requests=False):
    #TODO: proxy_host_dirs, log_requests
    routes = []

    if urlhandlers is not None:
        routes.extend(urlhandlers_to_routes(urlhandlers))

    if docroot is not None:
        routes.append(("GET", ".*", wpthandlers.file_handler))

    return server.WebTestHttpd(host, port, doc_root=docroot, routes=routes)
