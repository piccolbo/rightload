from sklearn.externals import joblib
import sklearn as sk
from warnings import warn
from featureextraction import entry2vec, url2vec


classifier_path = 'classifier.pickle'
try:
    classifier = joblib.load(classifier_path)
except IOError:
    warn("Creating new classifier")
    classifier = sk.linear_model.passive_aggressive.PassiveAggressiveClassifier(
    )


def score_entry(entry):
    X = entry2vec(entry)
    try:
        score = classifier.decision_function(X=[X])[0]
    except sk.exceptions.NotFittedError as e:
        score =  1
    return score

def score_feed(parsed_feed):
    return [score_entry(e) for e in parsed_feed.entries]

def learn_entry(feedback, url):
    X = url2vec(url)
    classifier.partial_fit(X=[X], y=[int(feedback)], classes=[0, 1])
    joblib.dump(classifier, classifier_path)
