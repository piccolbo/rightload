"""ML component."""
from feature_extraction import entry2mat, url2mat
from collections import namedtuple
from content_extraction import entry2url
from datastores import training_db, model_db
from flask import g
import gc
import logging as log
import numpy as np
# import sklearn.ensemble as sken
from sklearn import linear_model as lm

Feedback = namedtuple("Feedback", ["feedback", "explicit"])

# _memory = Memory(cachedir="score-cache", verbose=1, bytes_limit=10**9)

_model_attr_name = "_model"


def _set_model(model):
    setattr(g, _model_attr_name, model)
    model_db()["user"] = model
    model_db().sync()


def _get_model():
    return getattr(g, _model_attr_name, None) or model_db().get("user")


def _new_model():
    return lm.LogisticRegressionCV(
        class_weight='balanced', solver="sag", verbose=1, n_jobs=-1)
    # return sken.RandomForestClassifier(
    #     n_estimators=100,
    #     min_samples_split=.1,
    #     class_weight="balanced",
    #     oob_score=True,
    #     n_jobs=-1)


# @_memory.cache
def _score_entry(entry):
    url = entry2url(entry)
    try:
        X = entry2mat(entry, url)
        probs = _get_model().predict_proba(X=X)[:, 1]
        # implicit feedback: if not overridden we assume prediction correct
        store_feedback(url=url, feedback=probs.mean() > 0.5, explicit=False)
        return probs
    except Exception as e:
        log.error(
            ("Failed Scoring for {url}" + " because of exception {e}").format(
                url=url, e=e))
        raise


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


def store_feedback(url, feedback, explicit):
    """Store user feedback.

    Parameters
    ----------
    url : string
        URL of content feedback is about.
    feedback : string
        "l" or "d" for "like" or "dislike".
    explicit : bool
        Whether the feedback corresponded to an actual click or is indirect.

    Returns
    -------
    None

    """
    # explicit overwrites anything
    if (training_db().get(url) is None) or explicit:
        training_db()[url] = Feedback(feedback=feedback, explicit=explicit)
        training_db().sync()


def _url2mat_or_None(url):
    try:
        return url2mat(url)
    except Exception:
        return None


def learn():
    """Trigger the learning process.

    Returns
    -------
    string
        A message about the learning process containing a score.

    """
    Xy = [
        dict(X=X, y=[int(feedback)] * X.shape[0])
        for X, feedback in [(_url2mat_or_None(url), feedback)
                            for url, (feedback,
                                      _) in list(training_db().iteritems())]
        if X is not None
    ]
    X = np.concatenate([z['X'] for z in Xy], axis=0)
    y = np.concatenate([z['y'] for z in Xy], axis=0)
    # w = np.concatenate(
    #     [[1.0 / z['X'].shape[0]] * z['X'].shape[0] for z in Xyw], axis=0)
    del Xy
    gc.collect()  # Trying to get as much RAM as possible before model fit
    model = _new_model()
    model.fit(X=X, y=y)  # , sample_weight=w)

    _set_model(model)

    msg = "Classifier Score: {score}".format(score=model.score(X=X, y=y))
    log.info(msg)
    return msg
