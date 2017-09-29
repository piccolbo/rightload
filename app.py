#ingredients:   tinydb joblib.Memory
from flask import Flask, jsonify
import ml
import proxy as xy
from werkzeug.contrib.profiler import ProfilerMiddleware
import sys
import trace

# create a Trace object, telling it what to ignore, and whether to
# do tracing or line-counting or both.
_tracer = trace.Trace(
    ignoredirs=[sys.prefix, sys.exec_prefix], trace=1, count=0)

app = Flask(__name__)

# app.wsgiapp = ProfilerMiddleware(app.wsgiapp)


@app.route('/feed/<path:url>')
def _feed(url):
    return proxy(url)


@app.route('/feedback/<feedback>/<path:url>')
def _feedback(feedback, url):
    store_feedback(url=url, feedback=feedback == 'l', explicit=True)
    return ("Thank you", 204, {})


@app.route('/learn')
def _learn():
    learn()
    return ("Done", 204, {})
if __name__ == 'main':
    app.run()
