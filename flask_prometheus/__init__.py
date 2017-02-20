import time
import os

from prometheus_client import multiprocess, generate_latest
from prometheus_client import CollectorRegistry, Counter, Histogram
from flask import request, Response

FLASK_REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Flask Request Latency',
				['method', 'endpoint'])
FLASK_REQUEST_COUNT = Counter('flask_request_count', 'Flask Request Count',
				['method', 'endpoint', 'http_status'])

class Prometheus(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

        app.before_request(self.before_request)
        app.after_request(self.after_request)

        @app.route("/metrics", )
        def metrics():
            text = "# Process in {0}\n".format(os.getpid())
            return Response(text + generate_latest(registry), mimetype="text/plain")

    @staticmethod
    def before_request():
        request.start_time = time.time()

    @staticmethod  
    def after_request(response):
        request_latency = time.time() - request.start_time
        if 'metrics' not in request.url_rule.rule:
            FLASK_REQUEST_LATENCY.labels(request.method, request.path).observe(request_latency)
            FLASK_REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()

        return response
