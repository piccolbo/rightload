from boilerpipe.extract import Extractor
from joblib import Memory
import logging as log
import numpy as np
import requests


def _get_entry_content(entry):
    contents = [
        entry.get("description", ""),
        entry.get("content", [{}])[0].get("value", ""),
        entry.get("summary", "")
    ]
    return contents[np.argmax(map(len, contents))]


class FailedExtraction(Exception):
    pass


# see
# http://tomazkovacic.com/blog/2011/06/09/evaluating-text-extraction-algorithms/
def _scrape(url=None, html=None):
    assert (url != html)
    if html is not None:
        try:
            return Extractor(extractor='DefaultExtractor', html=html)
        except Exception as e:
            log.warn("can't extract {html}".format(html=html))
    else:
        try:
            return Extractor(extractor='DefaultExtractor', url=url)
        except Exception as e:
            log.warn("Can't extract {url} with boilerpipe".format(url=url))
            return _scrape(html=requests.get(url).content)


_memory = Memory(cachedir="content-cache", verbose=1, bytes_limit=10**9)


@_memory.cache(ignore=["entry"])
def url2html(url, entry=None):
    try:
        html = _scrape(url=url).getHTML()
    except Exception as e:
        log.warn("{url} can't be scraped\n".format(url=url))
        html = '<h1>{title}</h1>\n'.format(
            title=entry.title) + _get_entry_content(entry)
    if not html:
        log.error("Could not extract any html for for {url}".format(url=url))
        raise FailedExtraction
    return html


@_memory.cache(ignore=["entry"])
def url2text(url, entry=None):
    try:  # scrape url
        text = _scrape(url=url).getText()
        if len(text) < 40:
            raise FailedExtraction
    except Exception:  # scrape entry
        try:  # scrape entry content
            entry_content = _scrape(html=_get_entry_content(entry)).getText()
        except Exception:
            entry_content = ''
        text = (entry.title or '') + "." + (entry_content or '')
    if not text:
        log.error("Could not extract any text for {url}".format(url=url))
        raise FailedExtraction
    return text


# def entry2text(entry):
#     return url2text(entry.link, entry)
#

# def entry2html(entry):
#     return url2html(entry.link, entry)
