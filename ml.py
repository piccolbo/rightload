"""ML component."""
from content_extraction import get_url
from datastores import training_db, model_db
from feature_extraction import entry2mat, url2mat
from flask import g
from functools import wraps
import gc
from git import Repo
from inspect import signature
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
    """Return latest trained model.

    Returns
    -------
    Sklearn model (estimator)
        The most recent model.

    """
    return getattr(g, _model_attr_name, None) or model_db().get("user")


def _new_model(hidden_layer_sizes, max_iter):
    return MLPClassifier(
        hidden_layer_sizes=hidden_layer_sizes, solver="sgd", max_iter=max_iter
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


class DirtyRepoException(Exception):
    pass


def _mlflow_run(f, record_model=False):
    @wraps(f)
    def wrapper(*args, **kwargs):
        repo = Repo(".")
        if repo.is_dirty():
            log.error("repo is dirty, please check in all changes")
            raise DirtyRepoException
        with mlflow.start_run():
            mlflow.log_params(
                {
                    "commit": str(repo.head.commit),
                    "Function module": f.__module__,
                    "Function name": f.__qualname__,
                }
            )
            bound_args = signature(f).bind(*args, **kwargs)
            bound_args.apply_defaults()
            mlflow.log_params(bound_args.arguments)
            model = f(*args, **kwargs)
            if record_model:
                mlflow.log_model(model)
            return model

    return wrapper


@_mlflow_run
def learn(hidden_layer_sizes=(100, 100, 100), max_iter=1000):
    """Trigger the learning process.

    Returns
    -------
    string
        A message about the learning process containing a score.

    """
    log.info("Loading data")
    training_db_items = training_db().items()
    mlflow.log_metric("Number of articles", len(training_db_items))
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
    # w = np.concatenate([[1.0 / z["X"].shape[0]] * z["X"].shape[0] for z in Xy], axis=0)
    del Xy
    gc.collect()  # Trying to get as much RAM as possible before model fit
    log.info("Creating model")
    model = _new_model(hidden_layer_sizes=hidden_layer_sizes, max_iter=max_iter)
    log.info("Fitting model")
    log.info("Matrix size:" + str(X.shape))
    mlflow.log_metric("Number of sentences", X.shape[0])
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
    return model
