"""App start and route definitions."""
# ingredients:   tinydb joblib.Memory
from datastores import feed_db
from datetime import date, timedelta
from flask import Flask
from ml import store_feedback
from ml import learn
from proxy import proxy
import sys
import trace
import logging as log

#
# from rl_logging import decorate_all_in_module, log_on_fail
# import content_extraction as ce
#
#
# decorate_all_in_module(ce, log_on_fail)
#

# should be set at the project level
log.basicConfig(
    filename="./log", level=log.INFO, format="%(asctime)s %(levelname)s: %(message)s"
)

# create a Trace object, telling it what to ignore, and whether to
# do tracing or line-counting or both.
_tracer = trace.Trace(ignoredirs=[sys.prefix, sys.exec_prefix], trace=1, count=0)

app = Flask(__name__)

# app.wsgiapp = ProfilerMiddleware(app.wsgiapp)


@app.route("/feed/<path:url>")
def _feed(url):
    return proxy(url)


@app.route("/medium/<string:id>")
def _medium(id):
    return proxy("https://medium.com/feed/@" + id)


@app.route("/twitter/<string:id>")
def _twitter(id, date=lambda: (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")):
    date = date()
    return proxy(
        "https://twitrss.me/twitter_search_to_rss/"
        + "?term=from%3A{id}+since%3A{date}".format(id=id, date=date)
    )


@app.route("/feedback/<feedback>/<path:url>")
def _feedback(feedback, url):
    store_feedback(url=url, like=feedback == "l")
    log.info(
        u"storing feedback {feedback} for {url}".format(feedback=feedback, url=url)
    )
    return (
        """
    <!DOCTYPE html
           PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
           "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
    <head>
    <title>Thanks for your feedback</title>

    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
    </head>
    <body onload="self.close()">
    <h1>Thank you for your feedback, your filter has been updated</h1>
    </body>
    </html>
    """,
        200,
        {},
    )


@app.route("/learn")
def _learn():
    learn()
    return ("Done", 204, {})


@app.route("/preload")
def _preload():
    for url in feed_db().keys():
        try:
            proxy(url)
        except Exception:
            log.warning("Couldn't preload %s", url)
    return ("Done", 204, {})


if __name__ == "main":
    app.run()
