#rightload design

1. A component that downloads feeds from an opml file (feedcache, opml parser?)
2. A component that scores every item in each feed (goose + infersent + sklearn passive aggressive)
3. A component that filters them based on said score and serves them(plain python and flask)
3. A component that modifies filtered items injecting a feedback element(??)
4. A component that receives and uses said feedback(flask + goose + infersent + sklearn)


Useful libs:
Feedcache: feed parsing with caching https://doughellmann.com/blog/tag/feedcache/
goose: text extraction from URL instead of Beautiful Soup
infersent: vector sentence mapping
sklearn:  passive aggressive online learning
feedgenerator: feed generation
flask: web app framework http://flask.pocoo.org/docs/0.12/quickstart/
tinydb: for persistency -- may just use flat file at first
joblib.Memory: memoization -- stdlib may be enough but this is disk based, can be used for storage https://pythonhosted.org/joblib/memory.html
shelve: persistence https://docs.python.org/3/library/shelve.html

Links:
url encoding: https://stackoverflow.com/questions/40557606/how-to-url-encode-in-python-3
test feeds:
https://www.theregister.co.uk/Design/page/feeds.html
sklearn passive-aggressive algo:
http://scikit-learn.org/stable/modules/linear_model.html#passive-aggressive-algorithms
passive-aggressive paper:
http://jmlr.csail.mit.edu/papers/volume7/crammer06a/crammer06a.pdf
scikit on-line learning (partial_fit):
http://scikit-learn.org/stable/auto_examples/applications/plot_out_of_core_classification.html#sphx-glr-auto-examples-applications-plot-out-of-core-classification-py
Infersent:
https://github.com/facebookresearch/InferSent
sentence segmentation:
http://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.punkt
