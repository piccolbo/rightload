from content_extraction import get_text
from basilica import Connection
from joblib import Memory
from nltk.data import load as nltk_load
from numpy import array
from os import environ

_sent_detector = nltk_load("tokenizers/punkt/english.pickle")


_memory = Memory(cachedir="feature-cache-basilica", verbose=1, bytes_limit=10 ** 9)
_memory.reduce_size()


@_memory.cache(ignore=["entry"])
def entry2mat(entry, url):
    return _text2mat(get_text(entry=entry, url=url))


def url2mat(url):
    return entry2mat(None, url)


def text2sentences(text, max_sentences=300):  # limit to cap latency
    return _sent_detector.tokenize(text.strip())[:max_sentences]


def _text2mat(text):
    sentences = text2sentences(text)
    if len(sentences) == 0:
        raise FailedExtraction

    bkey = environ["BASILICA_KEY"]
    assert (
        bkey
    ), "Set the environment variable BASILICA_KEY to a key obtained from basilica.ai"

    if sentences:
        with Connection(bkey) as conn:
            return array(list(conn.embed_sentences(sentences)))
    else:
        raise FailedExtraction


class FailedExtraction(Exception):
    pass
