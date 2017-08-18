#ingredients:   tinydb joblib.Memory
from flask import Flask
import ml
import proxy as xy
from werkzeug.contrib.profiler import ProfilerMiddleware

app = Flask(__name__)
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)


@app.route('/feed/<path:url>')
def proxy(url):
    return xy.proxy(url)


@app.route('/learn/<feedback>/<path:url>')
def learn(feedback, url):
    ml.learn_entry(feedback == "l", url)
    return ("", 204, {})


if __name__ == 'main':
    app.run()
