"""
General organization of content extraction. Starting from an entry,
there are two avenues to get text out, one through the entry itself,
the other through its link. Also in the implementation different libs are applied, for now boilerpipe and textract, complicating the picture


"""
import BeautifulSoup as BS
from boilerpipe.extract import Extractor
import logging as log
import mimeparse
import re
from rl_logging import fun_name
import requests
from string import printable
import tempfile
import textract
from toolz.functoolz import excepts, partial
from urlextract import URLExtract


def get_html(url=None, entry=None):
    """
    Give me the content of the url or entry, to display in feed reader
    """
    assert url is not None or entry is not None
    return _url2html(url) if entry is None else _entry2html(entry)


def get_text(url=None, entry=None):
    """
    Give me text associated with url or entry, for display or ML use
    """
    if url is None:
        url = get_url(entry)
    return _warn_short(
        _keep_longest(
            lambda: _url2text(url),
            lambda: _entry2text(entry) if entry is not None else "",
        )
    )


def _entry2html(entry):
    return _entry2html_fields(entry)


def _entry2text(entry):
    return _html2text(_entry2html(entry))


def get_url(entry):
    url = entry.link
    return _entry2url_twitter(entry) if _is_twitter(url) else url


def _entry2url_twitter(entry):
    return _get_first_usable_url(_entry2html_fields(entry)) or entry.link


def _url2content(url, check_html=False):
    response = requests.get(url)
    doc_type = _get_doc_type(response)
    assert (not check_html) or (doc_type == "html")
    data = (
        unicode(response.content, encoding=response.encoding)
        if response.encoding is not None
        else response.content
    )
    return data, doc_type


def _url2html(url):
    return _keep_longest(
        lambda: _url2content(url, check_html=True), lambda: _url2html_bp(url)
    )


def _url2text(url):
    return _keep_first(
        lambda: _url2text_bp(url), lambda: _content2text_te(_url2content(url))
    )


def _html2text(html):
    return _keep_longest(
        lambda: _html2text_bp(html),
        lambda: _html2text_bs(html),
        lambda: _html2text_re(html),
    )


def _url2text_bp(url):
    return _bp_extractor(url=url).getText()


def _url2html_bp(url):
    return _bp_extractor(url=url).getHTML()


def _html2text_bp(html):
    return _bp_extractor(html=html).getText()


def _html2text_bs(html):
    return BS.BeautifulSoup(html).getText()


def _html2text_re(html):
    return " ".join(re.split(pattern="<.*?>", string=html))


def _content2text_te(content):
    data, doc_type = content
    with tempfile.NamedTemporaryFile(mode="wb", suffix="." + doc_type) as fh:
        fh.write(data)
        fh.flush()
        return unicode(textract.process(fh.name, encoding="utf-8"), encoding="utf-8")


def _bp_extractor(**kwargs):
    """Accepted args url or html"""
    return Extractor(extractor="DefaultExtractor", **kwargs)


def _entry2html_fields(entry):
    title = entry.get("title", "")
    content = max(
        [
            entry.get("description", ""),
            entry.get("content", [{}])[0].get("value", ""),
            entry.get("summary", ""),
        ],
        key=len,
    )
    return title + "." + content


def _get_doc_type(response):
    return mimeparse.parse_mime_type(response.headers["Content-Type"])[1]


def handler(ex, fun, default):
    log.warning(fun_name(fun) + " failed")
    return default


def _keep_longest(*strategies):

    return max(_keep_all(*strategies), key=len)


def _keep_all(*strategies):

    return map(
        lambda fun: excepts(Exception, fun, partial(handler, fun=fun, default=""))(),
        strategies,
    )


def _keep_first(*strategies):
    for fun in strategies:
        retval = excepts(Exception, fun, partial(handler, fun=fun, default=None))()
        if retval is not None:
            return retval
        else:
            log.warning(fun_name(fun) + " failed")
        raise FailedExtraction()


def _is_twitter(url):
    return bool(re.search(r"twitter.com", url))  # quick and dirty


def _is_image(url):
    return url.split("/")[-1].split(".")[-1] in set(["jpg", "jpeg", "png"])


def _get_first_usable_url(text):
    s = [
        url
        for url in URLExtract().find_urls(text)
        if not _is_twitter(url) and not _is_image(url)
    ]
    return filter(lambda x: x in set(printable), s[0]) if len(s) > 0 else None


def _warn_short(text):
    if len(text) < 40:
        log.warning("Minimal text extracted")
    return text


class FailedExtraction(Exception):
    pass
