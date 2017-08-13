from sklearn.externals import joblib
import sklearn as sk
from warnings import warn
from featureextraction import url2vec

classifier_path = 'classifier.pickle'
try:
    classifier = joblib.load(classifier_path)
except IOerror:
    warn("Creating new classifier")
    classifier = sk.linear_model.passive_aggressive.PassiveAggressiveClassifier(
    )


def score_entry(entry):
    X = url2vec(entry.link)
    return classifier.decision_function(
        X=X)[0] if classifier is not None else 1

def score_feed(parsed_feed):
    return [score_entry(e) for e in parsed_feed.entries]

def learn_entry(feedback, url):
    X = url2vec(url)
    classifier.partial_fit(X=X, y=[int(feedback)], classes=[0, 1])
    joblib.dump(classifier, classifier_path)
