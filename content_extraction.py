"""
General organization of content extraction.

we have datatypes like entry url content html and text
we have extractors between these types, some of which are not really extractors but we'll stick with that name
when we have multiple approaches at a conversion we aggregate the result with keep_first
in recognition of the fact that extractors can fail, they are in charge of catching own exceptions and returning ""

when  multiple ways of getting
logging is taken care of elsewhere, but all exceptions are logged

"""
import BeautifulSoup as BS
from boilerpipe.extract import Extractor
from functools import wraps
import logging as log
import mimeparse
import re
from rl_logging import log_call
import requests
from string import printable
import tempfile
import textract
from toolz.functoolz import partial
from urlextract import URLExtract


# this defines a partially FailedExtraction, justifies using an alternate method
# but not raising an exception
SHORT_TEXT = 40


def extractor(fun):
    """An extractor doesn't fail, it logs instead and returns "".
    """

    @wraps(fun)
    def decorated(*args, **kwargs):
        try:
            return _warn_short(fun(*args, **kwargs))
        except Exception as e:
            log_call(fun, args, kwargs, exception=e)
            return ""

    return decorated


@extractor
def _keep_first(*strategies, **kwargs):
    """Try strategies (argumentless callables) in order provided.

    If extraction exceeds supplied min_length, return, else try next.
    If all strategies have been attempted, return longest extraction."""

    min_length = kwargs.get("min_length", SHORT_TEXT)
    longest = ""
    for fun in strategies:
        retval = fun()
        if retval is not None and len(retval) >= min_length:
            return retval
        if len(retval) > len(longest):
            longest = retval
    return _warn_short(longest, min_length)


@extractor
def get_html(url=None, entry=None):
    """
    Give me the content of the url or entry, to display in feed reader
    """
    url, entry = _process_get_args(url, entry)
    # prefer url access as it goes to real content. Feed entry is often abridged.
    return _keep_first(lambda: _url2html(url), lambda: _entry2html(entry))


@extractor
def get_text(url=None, entry=None):
    """
    Give me text associated with url or entry, for display or ML use
    """
    url, entry = _process_get_args(url, entry)
    return _keep_first(lambda: _url2text(url), lambda: _entry2text(entry))


def _process_get_args(url, entry):
    assert url is not None or entry is not None
    if url is None:
        url = get_url(entry)
    return url, entry


@extractor
def _entry2text(entry):
    return _html2text(_entry2html(entry))


def get_url(entry):
    url = entry.link
    return _entry2url_twitter(entry) if _is_twitter(url) else url


def _entry2url_twitter(entry):
    return _get_first_usable_url(_entry2html(entry)) or entry.link


# this needs a custom dec because of return type
@extractor
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


@extractor
def _url2html(url):
    return _keep_first(
        lambda: lambda: _bp_extractor(url=url).getHTML(),
        _url2content(url, check_html=True),
    )


@extractor
def _url2text(url):
    return _keep_first(
        lambda: _bp_extractor(url=url).getText(),
        lambda: _content2text_te(_url2content(url)),
    )


@extractor
def _html2text(html):
    return _keep_first(
        lambda: _bp_extractor(html=html).getText(),
        lambda: BS.BeautifulSoup(html).getText(),
        lambda: " ".join(re.split(pattern="<.*?>", string=html)),
    )


@extractor
def _content2text_te(content):
    data, doc_type = content
    with tempfile.NamedTemporaryFile(mode="wb", suffix="." + doc_type) as fh:
        fh.write(data)
        fh.flush()
        return unicode(textract.process(fh.name, encoding="utf-8"), encoding="utf-8")


def _bp_extractor(**kwargs):
    """Accepted args url or html"""
    return Extractor(extractor="DefaultExtractor", **kwargs)


@extractor
def _entry2html(entry):
    title = entry.get("title", "")
    content = max(
        [
            entry.get("description", ""),
            entry.get("content", [{}])[0].get("value", ""),
            entry.get("summary", ""),
        ],
        key=len,
    )
    # TODO: would it be possible to grab the title for use in other types of extraction?
    return title + "." + content


def _get_doc_type(response):
    return mimeparse.parse_mime_type(response.headers["Content-Type"])[1]


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


def _warn_short(what, min_length=SHORT_TEXT):
    text = what if isinstance(what, basestring) else what[0]
    # if len(text) < min_length:
    # log.warning(
    #     "".join(tb.format_stack()[-10:]) + "Minimal text extracted: " + text
    # )
    return text
