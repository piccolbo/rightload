"""Feature extraction turn texts into matrices."""
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
    """Transform a feed entry into a matrix.

    Only one of the two parameters needs to be supplied.

    Parameters
    ----------
    entry : feedcache feed entry
        The entry to transform.
    url : type
        The url pointing to the content of the entry .

    Returns
    -------
    numpy matrix
        A matrix representation of the entry content.

    """
    return _text2mat(get_text(entry=entry, url=url))


def url2mat(url):
    """Transform a url pointing to some content into a matrix.

    Parameters
    ----------
    url : str
        The URL pointing to the content.

    Returns
    -------
    Numpy Matrix
        The matrix representation of the content identified by the URL.

    """
    return entry2mat(None, url)


def text2sentences(text, max_sentences=300):  # limit to cap latency
    """Split a text into sentences.

    Parameters
    ----------
    text : str
        The text to split.

    max_sentences: int
        The maximum number of sentences to return.
    Returns
    -------
    list of str
        A list of the sentences contained in the text.

    """
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
    """Exception to be raised when extraction fails."""

    pass
