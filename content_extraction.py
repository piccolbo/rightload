# -*- coding: utf-8 -*-
from boilerpipe.extract import Extractor
from joblib import Memory
import logging as log
import numpy as np
import re
import requests


def _get_entry_content(entry):
    contents = [
        entry.get("description", ""),
        entry.get("content", [{}])[0].get("value", ""),
        entry.get("summary", "")
    ]
    return contents[np.argmax(map(len, contents))]


def _get_first_url(content):
    REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""

    return re.search(REGEX, content).group()


def _is_twitter(url):
    return bool(re.search(r'twitter.com', url))  # quick and dirty


def _escape_twitter(url):
    # work in progress
    if not _is_twitter(url):
        return url
    else:
        try:
            return _get_first_url(_url2text(url))
        except Exception:
            return url


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
            log.warn("Can't extract html from {html}".format(html=html))
    else:
        try:
            return Extractor(extractor='DefaultExtractor', url=url)
        except Exception as e:
            log.warn(
                "Can't extract from {url} with boilerpipe".format(url=url))
            return _scrape(html=requests.get(url).content)


_memory = Memory(cachedir="content-cache", verbose=1, bytes_limit=10**9)


def entry2url(entry):
    url = entry.link
    if _is_twitter(url):
        try:
            content = _get_entry_content(entry)
            url = _get_first_url(content)
        except Exception:
            pass
    return url


def entry2html(entry):
    return _url2html(entry2url(entry), entry)


def entry2text(entry):
    url = entry2url(entry)
    return _url2text(None, entry) if _is_twitter(url) else _url2text(
        url, entry)


@_memory.cache(ignore=["entry"])
def _url2html(url, entry=None):
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
def _url2text(url, entry=None):
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
