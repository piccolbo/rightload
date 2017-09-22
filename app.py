#ingredients:   tinydb joblib.Memory
from flask import Flask, jsonify
import ml
import proxy as xy
from werkzeug.contrib.profiler import ProfilerMiddleware
import sys
import trace

# create a Trace object, telling it what to ignore, and whether to
# do tracing or line-counting or both.
tracer = trace.Trace(
    ignoredirs=[sys.prefix, sys.exec_prefix], trace=1, count=0)

app = Flask(__name__)

# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)


@app.route('/feed/<path:url>')
def feed(url):
    return xy.proxy(url)


@app.route('/feedback/<feedback>/<path:url>')
def feedback(feedback, url):
    ml.store_feedback(url=url, feedback=feedback, explicit=True)
    return ("Thank you", 204, {})

@app.route('/learn')
def learn():
    ml.learn()
    return ("Done", 204, {})
if __name__ == 'main':
    app.run()
