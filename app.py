#ingredients:   tinydb joblib.Memory
from flask import Flask
from datastores import training_db, classifier_db, feature_db
import ml
import proxy as xy
from werkzeug.contrib.profiler import ProfilerMiddleware

app = Flask(__name__)

# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

@app.route('/feed/<path:url>')
def feed(url):
    return xy.proxy(url, training_db(), classifier_db(), feature_db())


@app.route('/feedback/<feedback>/<path:url>')
def feedback(feedback, url):
    ml.store_feedback(feedback == "l", url, training_db())
    return ("Thank you", 204, {})


@app.route('/learn')
def learn():
    ml.learn(training_db(), classifier_db(), feature_db())
    return ("Done", 204, {})


if __name__ == 'main':
    app.run()
