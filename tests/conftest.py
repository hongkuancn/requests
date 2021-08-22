# -*- coding: utf-8 -*-

try:
    from http.server import HTTPServer
    from http.server import SimpleHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler 

import ssl
import tempfile
import threading

import pytest
from requests.compat import urljoin
import trustme


def prepare_url(value):
    # Issue #1483: Make sure the URL always has a trailing slash
    httpbin_url = value.url.rstrip('/') + '/'

    def inner(*suffix):
        return urljoin(httpbin_url, '/'.join(suffix))

    return inner


# WHY 没有明白参数httpbin是在哪里赋值的，port此时就会有值。这个方法会在test前执行。
# 似乎是在env/lib/python3.8/site-packages/pytest_httpbin/plugin.py执行的
@pytest.fixture
def httpbin(httpbin):
    return prepare_url(httpbin)


@pytest.fixture
def httpbin_secure(httpbin_secure):
    return prepare_url(httpbin_secure)


@pytest.fixture
def nosan_server(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("certs")
    ca = trustme.CA()
    # only commonName, no subjectAltName
    server_cert = ca.issue_cert(common_name=u"localhost")
    ca_bundle = str(tmpdir / "ca.pem")
    ca.cert_pem.write_to_path(ca_bundle)

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_cert.configure_cert(context)
    server = HTTPServer(("localhost", 0), SimpleHTTPRequestHandler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    yield "localhost", server.server_address[1], ca_bundle

    server.shutdown()
    server_thread.join()
