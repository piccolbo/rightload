"""ML component."""
from content_extraction import get_url
from datastores import training_db, model_db
from feature_extraction import entry2mat, url2mat
from flask import g
import gc
from git import Repo
import logging as log
import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.neural_network import MLPClassifier

_model_attr_name = "_model"


def _set_model(model):
    setattr(g, _model_attr_name, model)
    model_db()["user"] = model
    model_db().sync()


def get_model():
    return getattr(g, _model_attr_name, None) or model_db().get("user")


def _new_model():
    # 3 400 layer best so far
    hidden_layer_sizes = (200, 200, 200)
    mlflow.log_param("hidden layer sizes", hidden_layer_sizes)
    return MLPClassifier(
        hidden_layer_sizes=hidden_layer_sizes, solver="sgd", early_stopping=False
    )


def _score_entry(entry):
    url = get_url(entry)
    try:
        X = entry2mat(entry, url)
        model = get_model()
        probs = model.predict_proba(X=X)
        return probs[:, 1]
    except Exception as e:
        log.error(
            ("Failed Scoring for {url}" + " because of exception {e}").format(
                url=url, e=e
            )
        )
        return None


def score_feed(parsed_feed):
    """Score each entry in a feed.

    Parameters
    ----------
    parsed_feed : Feedparser feed
        The feed whose entries are to be scored.

    Returns
    -------
    type
        A list of scores, one per entry. Higher score means more likely to
        receive positive feedback.

    """
    return [_score_entry(e) for e in parsed_feed.entries]


def store_feedback(url, like):
    """Store user feedback.

    Parameters
    ----------
    url : string
        URL of content feedback is about.
    like : bool
        True for like, False for dislike.

    Returns
    -------
    None

    """

    training_db()[url] = like
    training_db().sync()


def _url2mat_or_None(url):
    try:
        return url2mat(url)
    except Exception:
        # del training_db()[url] this is too hasty, erasing valuable human
        # feedback
        # training_db().sync()
        return None


def learn():
    """Trigger the learning process.

    Returns
    -------
    string
        A message about the learning process containing a score.

    """
    with mlflow.start_run():
        repo = Repo(".")
        mlflow.log_param("commit", str(repo.head.commit))
        log.info("Loading data")
        training_db_items = training_db().items()
        mlflow.log_param("Number of articles", len(training_db_items))
        Xy = [
            dict(X=X, y=[int(like)] * X.shape[0])
            for X, like in [
                (_url2mat_or_None(url), like) for url, like in training_db_items
            ]
            if (X is not None)
        ]
        log.info("Forming matrices")
        X = np.concatenate([z["X"] for z in Xy], axis=0)
        y = np.concatenate([z["y"] for z in Xy], axis=0)
        w = np.concatenate(
            [[1.0 / z["X"].shape[0]] * z["X"].shape[0] for z in Xy], axis=0
        )
        del Xy
        gc.collect()  # Trying to get as much RAM as possible before model fit
        log.info("Creating model")
        model = _new_model()
        log.info("Fitting model")
        log.info("Matrix size:" + str(X.shape))
        mlflow.log_param("Number of sentences", X.shape[0])
        model.fit(X=X, y=y)  # , sample_weight=w)
        _set_model(model)
        score = model.score(X=X, y=y)
        log.info(f"Classifier Score: {score}")
        mlflow.log_metric("score", score)
        scores = cross_val_score(
            model, X, y, n_jobs=-1, cv=StratifiedKFold(n_splits=10, shuffle=True)
        )
        mlflow.log_metric("Median CV score", np.median(scores))
        mlflow.log_metric("IQR CV score", np.subtract(*np.percentile(scores, [75, 25])))
        log.info("Cross Validation Scores: {scores}".format(scores=scores))
    return '<h1>Done!</h1> run mlflow ui --port 5555 and go to <a href="http://127.0.0.1:5555">here</a> to check results'
