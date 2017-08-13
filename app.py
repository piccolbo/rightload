#ingredients: Feedcache goose infersent sklearn passive aggressive feedgen  tinydb joblib.Memory
from flask import Flask
import proxy as xy

app = Flask(__name__)

@app.route('/feed/<path:url>')
def proxy(url):
    return xy.proxy(url)

@app.route('/learn/<feedback>/<path:url>')
def learn(feedback, url):
    ml.learn(feedback == "l", url)

if __name__ == 'main':
    app.run()
