import os
import sys
from urllib.parse import parse_qs, urlencode

# Ensure root directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

# WSGI middleware to normalize PATH_INFO for Vercel serverless rewrites
class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        if '__path' in query_string:
            params = parse_qs(query_string, keep_blank_values=True)
            if '__path' in params:
                dest_path = params.pop('__path')[0].lstrip('/')
                environ['PATH_INFO'] = '/' + dest_path
                environ['QUERY_STRING'] = urlencode(params, doseq=True)
        elif environ.get('PATH_INFO') in ('/api/index', '/api/index.py'):
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
