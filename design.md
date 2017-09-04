#rightload design

## Components

1. A component that downloads feeds from an opml file (feedcache, opml parser?) DELAYED
2. A component that scores every item in each feed (goose + infersent + sklearn passive aggressive) DONE
3. A component that filters them based on said score and serves them(plain python and flask) Just scoring
3. A component that modifies filtered items injecting a feedback element DONE
4. A component that receives and uses said feedback(flask + goose + infersent + sklearn) DONE

## URL design

|*uuid*|operation|item|*path*|retval|
|---|---|---|---|---|
|*uuid*|score-url||*path*|JSON|
|*uuid*|learn|feedback|*path*|empty
|*uuid*|score-feed||*path*|JSON
|*uuid*|feedproxy||*path*|XML|
|*uuid*|webproxy||*path*|html
|||||


###Useful libs:
* Feedcache: feed parsing with caching https://doughellmann.com/blog/tag/feedcache/
* goose: text extraction from URL instead of Beautiful Soup
* infersent: vector sentence mapping
* sklearn:  passive aggressive online learning
* feedgenerator: feed generation
* flask: web app framework http://flask.pocoo.org/docs/0.12/quickstart/
* tinydb: for persistency -- may just use flat file at first
* joblib.Memory: memoization -- stdlib may be enough but this is disk based, can be used for storage https://pythonhosted.org/joblib/memory.html
shelve: persistence https://docs.python.org/3/library/shelve.html

### Links
* url encoding: https://stackoverflow.com/questions/40557606/how-to-url-encode-in-python-3
* test feeds:
https://www.theregister.co.uk/Design/page/feeds.html
* sklearn passive-aggressive algo:
http://scikit-learn.org/stable/modules/linear_model.html#passive-aggressive-algorithms
* passive-aggressive paper:
http://jmlr.csail.mit.edu/papers/volume7/crammer06a/crammer06a.pdf
* scikit on-line learning (partial_fit):
http://scikit-learn.org/stable/auto_examples/applications/plot_out_of_core_classification.html#sphx-glr-auto-examples-applications-plot-out-of-core-classification-py
* Infersent:
https://github.com/facebookresearch/InferSent
* sentence segmentation:
http://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.punkt
* uuid generator: https://www.uuidgenerator.net/
* custom atom elements: http://www.odata.org/documentation/odata-version-2-0/atom-format/
* custom rss elements http://www.disobey.com/detergent/2002/extendingrss2/
