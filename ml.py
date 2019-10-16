"""ML component."""
from feature_extraction import entry2mat, url2mat
from content_extraction import get_url
from datastores import training_db, model_db
from flask import g
import gc
import logging as log
import numpy as np

# import sklearn.ensemble as sken

from sklearn.linear_model import LogisticRegressionCV

_model_attr_name = "_model"


def _set_model(model):
    setattr(g, _model_attr_name, model)
    model_db()["user"] = model
    model_db().sync()


def get_model():
    return getattr(g, _model_attr_name, None) or model_db().get("user")


def _new_model():
    return LogisticRegressionCV(
        solver="sag",
        scoring="accuracy",
        verbose=0,
        n_jobs=1,
        Cs=[1.0],
        cv=20,
        class_weight="balanced",
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
            (u"Failed Scoring for {url}" + u" because of exception {e}").format(
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
    log.info("Loading data")
    Xy = [
        dict(X=X, y=[int(like)] * X.shape[0])
        for X, like in [
            (_url2mat_or_None(url), like) for url, like in training_db().items()
        ]
        if (X is not None)
    ]
    log.info("Forming matrices")
    X = np.concatenate([z["X"] for z in Xy], axis=0)
    y = np.concatenate([z["y"] for z in Xy], axis=0)
    del Xy
    gc.collect()  # Trying to get as much RAM as possible before model fit
    log.info("Creating model")
    model = _new_model()
    log.info("Fitting model")
    log.info("Matrix size:" + str(X.shape))
    model.fit(X=X, y=y)
    _set_model(model)
    log.info("Classifier Score: {score}".format(score=model.score(X=X, y=y)))
    log.info("Cross Validation Score: {score}".format(score=model.scores_))
    log.info("Regularization: best C ={C}, Cs = {Cs}".format(C=model.C_, Cs=model.Cs_))
