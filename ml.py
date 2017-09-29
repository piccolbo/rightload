from feature_extraction import url2vec
from collections import namedtuple
from content_extraction import FailedExtraction
from datastores import training_db, model_db
from debug import spy
from flask import g
import numpy as np
import os
import sklearn.linear_model as lm
import sklearn as sk
from time import sleep
import traceback
from warnings import warn

Feedback = namedtuple("Feedback", ["feedback", "explicit"])


_model_attr_name = "_model"

def _set_model(model):
    setattr(g, _model_attr_name, model)
    model_db()["user"] = model
    model_db().sync()


def _get_model():
    model = getattr(g, _model_attr_name, None)
    if model is None:
        model = model_db().get("user", None)
        if model is None:
            model = _new_model()
        _set_model(model)
    return model


def _new_model():
    return lm.LogisticRegression(class_weight='balanced', solver = "saga")


def _score_entry(entry):
    try:
        X = url2vec(entry.link, entry)
        probs = _get_model().predict_proba(X=X)[:, 1]
        #implicit feedback: if not overridden we assume prediction correct
        store_feedback(
            url=entry.link, feedback=probs.mean() > 0.5, explicit=False)
        return probs
    except Exception, e:
        warn("Failed Scoring")
        warn(entry.link)
        warn(traceback.format_exc())
        raise


def score_feed(parsed_feed):
    return [_score_entry(e) for e in parsed_feed.entries]


def store_feedback(url, feedback, explicit):
    # explicit overwrites anything
    # implicit overwrites implicit
    current_value = training_db().get(url)
    if (current_value is None) or (not current_value.explicit) or explicit:
        training_db()[url] = Feedback(feedback=feedback, explicit=explicit)
        training_db().sync()


def _url2vec_or_None(url):
    try:
        return url2vec(url)
    except:
        return None


def learn():
    Xy = [(X, [int(feedback)] * X.shape[0])
          for X, feedback in [(_url2vec_or_None(url), feedback)
                              for url, (feedback,
                                        _) in list(training_db().iteritems())]
          if X is not None]
    X = np.concatenate([X_ for X_, _ in Xy], axis=0)
    y = np.concatenate([y_ for _, y_ in Xy], axis=0)
    model = _new_model()
    model.fit(X=X, y=y)

    _set_model(model)

    msg = "Classifier Score: {score}".format(score=model.score(X=X, y=y))
    print msg
    return msg
