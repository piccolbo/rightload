from featureextraction import url2vec, FailedExtraction
import numpy
import sklearn.linear_model as lm
import sklearn as sk
from sklearn.externals import joblib
import traceback
from warnings import warn

user = 'piccolbo@gmail.com'


def score_entry(entry, classifier_db, feature_db):
    try:
        X = url2vec(entry.link, feature_db, entry)
        probs = classifier_db[user].predict_proba(X=X)
        return probs[:, 1].mean()
    except Exception, e:
        warn("Failed Scoring")
        warn(entry.link)
        warn(traceback.format_exc())
        return 0.5


def score_feed(parsed_feed, classifier_db, feature_db):
    return [score_entry(e, classifier_db, feature_db) for e in parsed_feed.entries]


def store_feedback(feedback, url, training_db):
    training_db[url] = feedback
    training_db.sync()


def store_unlabelled(url, training_db):
    if not training_db.has_key[url]:
        training_db[url] = None
        training_db.sync()


def url2vec_or_None(url, feature_db):
    try:
        return url2vec(url, feature_db)
    except:
        return None


def learn(training_db, classifier_db, feature_db):
    classifier = lm.LogisticRegressionCV()
    Xy = [(X, [int(feedback)] * X.shape[0])
          for X, feedback in [(url2vec_or_None(url, feature_db), feedback)
                              for url, feedback in training_db.iteritems()]
          if X is not None]
    X = numpy.concatenate([X_ for X_, _ in Xy], axis=0)
    y = numpy.concatenate([y_ for _, y_ in Xy], axis=0)
    classifier.fit(X=X, y=y)
    warn("Classifier Score: {score}".format(score=classifier.score(X=X, y=y)))
    classifier_db[user] = classifier
    classifier_db.sync()
