import logging

from flask import Flask, request, Response
from flask.logging import default_handler
from spectator import Config, Registry, StopWatch

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(default_handler)
APP_1OR2 = "app2"

## SEE DOCS
"""
docs/spectator/lang/py/meters/age-gauge.md
docs/spectator/lang/py/meters/counter.md
docs/spectator/lang/py/meters/dist-summary.md
docs/spectator/lang/py/meters/gauge.md
docs/spectator/lang/py/meters/max-gauge.md
docs/spectator/lang/py/meters/monotonic-counter-uint.md
docs/spectator/lang/py/meters/monotonic-counter.md
docs/spectator/lang/py/meters/percentile-dist-summary.md
docs/spectator/lang/py/meters/percentile-timer.md
docs/spectator/lang/py/meters/timer.md
docs/spectator/lang/py/migrations.md
docs/spectator/lang/py/perf-test.md
docs/spectator/lang/py/usage.md
"""

if APP_1OR2 == "app1":
    registry = Registry()

    app = Flask(__name__)

    @app.route("/")
    def root():
        return Response("Usage: /api/v1/play?country=foo&title=bar")

    @app.route("/api/v1/play")
    def play():
        country = request.args.get("country", default="unknown")
        title = request.args.get("title", default="unknown")

        if country == "unknown" or title == "unknown":
            status = 404
            message = f"invalid play request for country={country} title={title}"
        else:
            status = 200
            message = f"requested play for country={country} title={title}"

        tags = {"path": "v1_play", "country": country, "title": title, "status": str(status)}
        registry.counter("server.requestCount", tags).increment()
        return Response(message, status=status)
elif APP_1OR2 == "app2":
    config = Config(extra_common_tags={"platform": "flask-demo"})
    registry = Registry(config)

    request_count_id = registry.new_id("server.requestCount", {"path": "v1_play"})
    request_latency = registry.timer("server.requestLatency", {"path": "v1_play"})
    response_size = registry.distribution_summary("server.responseSize", {"path": "v1_play"})

    app = Flask(__name__)

    @app.route("/")
    def root():
        return Response("Usage: /api/v1/play?country=foo&title=bar")

    @app.route("/api/v1/play")
    def play():
        with StopWatch(request_latency):
            country = request.args.get("country", default="unknown")
            title = request.args.get("title", default="unknown")

            if country == "unknown" or title == "unknown":
                status = 404
                message = f"invalid play request for country={country} title={title}"
            else:
                status = 200
                message = f"requested play for country={country} title={title}"

            tags = {"country": country, "title": title, "status": str(status)}
            request_count = registry.counter_with_id(request_count_id.with_tags(tags))

            request_count.increment()
            response_size.record(len(message))

            return Response(message, status=status)

"""
flask --app app run
"""
