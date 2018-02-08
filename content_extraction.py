# -*- coding: utf-8 -*-
from boilerpipe.extract import Extractor
import logging as log
import mimeparse
import numpy as np
import re
import requests
from urlextract import URLExtract
import textract
import tempfile


def _get_entry_content(entry):
    contents = [
        entry.get("description", ""),
        entry.get("content", [{}])[0].get("value", ""),
        entry.get("summary", "")
    ]
    return contents[np.argmax(map(len, contents))]


def _get_first_non_twitter_url(text):
    return [
        url for url in URLExtract().find_urls(text) if not _is_twitter(url)
    ][0]


def _is_twitter(url):
    return bool(re.search(r'twitter.com', url))  # quick and dirty


class FailedExtraction(Exception):
    pass


# see
# http://tomazkovacic.com/blog/2011/06/09/evaluating-text-extraction-algorithms/
def _scrape_html(html):
    try:
        return Extractor(extractor='DefaultExtractor', html=html)
    except Exception as e:
        log.warn("Can't extract from" +
                 " {html} with boilerpipe because of exception {e}".format(
                     html=html[:800], e=e))
        raise FailedExtraction


def _scrape_url(url):
    try:
        return Extractor(extractor='DefaultExtractor', url=url)
    except Exception as e:
        log.warn("Can't extract from" +
                 " {url} with boilerpipe because of exception {e}".format(
                     url=url, e=e))
        raise


def _scrape2text(url):
    response = requests.get(url)
    doc_type = mimeparse.parse_mime_type(response.headers['Content-Type'])[1]
    with tempfile.NamedTemporaryFile(mode="wb", suffix="." + doc_type) as fh:
        fh.write(response.content)
        fh.flush()

        def fail():
            raise FailedExtraction

        return {
            'html': lambda: _scrape_html(response.content).getText(),
            'gif': fail,
            'jpg': fail,
            'png': fail
        }.get(doc_type, lambda: unicode(textract.process(fh.name)))()


def entry2url(entry):
    url = entry.link
    if _is_twitter(url):
        try:
            url = _get_first_non_twitter_url(_get_entry_content(entry))
        except IndexError:
            pass
        except Exception as e:
            log.warn((u"Can't get external link from {url} " +
                      "because of exception {e}").format(url=url, e=e))
    return url


def entry2html(entry):
    url = entry2url(entry)
    return _url2html(None, entry) if _is_twitter(url) else _url2html(
        url, entry)


def entry2text(entry):
    url = entry2url(entry)
    return _url2text(None, entry) if _is_twitter(url) else _url2text(
        url, entry)


def _url2html(url, entry=None):
    try:
        html = _scrape_url(url).getHTML()
    except Exception as e:
        log.warn("{url} can't be scraped because of exception {e}".format(
            url=url, e=e))
        html = '<h1>{title}</h1>\n'.format(
            title=entry.title) + _get_entry_content(entry)
    if not html:
        log.error("Could not extract any html for for {url}".format(url=url))
        raise FailedExtraction
    return html


def _check_short(text):
    if len(text) < 40:
        raise FailedExtraction


def _url2text(url, entry=None):
    try:  # scrape url with boilerpipe
        text = _scrape_url(url).getText()
        _check_short(text)
    except Exception:
        try:  # scrape with textract
            text = _scrape2text(url)
            _check_short(text)
        except Exception:
            try:  # scrape entry content
                entry_content = _scrape_html(
                    _get_entry_content(entry)).getText()
            except Exception:
                entry_content = ''
            text = (entry.title or '') + "." + (entry_content or '')
    if not text:
        log.error("Could not extract any text for {url}".format(url=url))
        raise FailedExtraction
    return text
