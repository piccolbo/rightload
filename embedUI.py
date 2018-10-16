"""Insert feedback UI in feed entry."""
import BeautifulSoup as bs
from content_extraction import entry2url, entry2text
from colour import Color
from feature_extraction import text2sentences
from flask import request
from fuzzywuzzy import fuzz
import logging as log
import numpy as np
from traceback import format_exc


def _feedbackurl(link, well_spent):
    return (
        u"http://"
        + request.host
        + u"/feedback/"
        + (u"l" if well_spent else u"d")
        + u"/"
        + link
    )


def _is_long(text):
    return len(text) > 1000


def _p(style, text):
    return u'<p style="{style}">{text}</p>'.format(style=style, text=text)


def _a(href, target, text):
    return u'<a href="{href}" target="{target}">{text}</a>'.format(
        href=href, target=target, text=text
    )


def _font(color, text):
    return u'<font color="{color}">{text}</font>'.format(color=color, text=text)


def _span(text, color):
    # style = u'"border-bottom: 3px solid {color}"'
    # style = u'"text-decoration: underline; text-decoration-color: {color}"'
    style = u'"background-color: {color};  line-height: auto"'
    style = style.format(color=color)
    return u"<span style={style}>{text}</span>".format(text=text, style=style)


def _feedback_link(is_good, content_link):
    return _a(
        href=_feedbackurl(link=content_link, well_spent=is_good),
        target=u"_top",
        text=_font(
            color=u"green" if is_good else u"red",
            text=u"Time Well Spent" if is_good else u"Time Wasted",
        ),
    )


def _conditional_bar(mean_score, content_link):
    return _p(
        style=u"BACKGROUND-COLOR: #DBDBDB",
        text=(_feedback_link(True, content_link) if mean_score <= 0.5 else u"")
        + (u" or " if mean_score == 0.5 else u"")
        + (_feedback_link(False, content_link) if mean_score >= 0.5 else u""),
    )


def _add_bar(text, mean_score, content_link):
    bar = _conditional_bar(mean_score, content_link)
    return bar + text + (bar if _is_long(text) else u"")


def _embedUI_entry(entry, score):
    mean_score = score.mean()
    # body = entry2text(entry)
    body = _highlight_text(entry2text(entry), score)
    # body = entry2html(entry)
    # body = _highlight_html(html, text, score) #broken
    url = entry2url(entry)
    if u"description" in entry:
        entry[u"description"] = _add_bar(body, mean_score, url)
    if u"content" in entry:
        entry[u"content"][0].value = _add_bar(body, mean_score, url)
    if u"title" in entry:
        entry[u"title"] = u"{mean_score:} | {title}".format(
            mean_score=int(mean_score * 100), title=entry[u"title"]
        )
    return entry


def embedUI(parsed_feed, score):
    """Insert a UI element in each entry of a feed.

    Parameters
    ----------
    parsed_feed : feedparser.
        Description of parameter `parsed_feed`.
    score : type
        Description of parameter `score`.

    Returns
    -------
    type
        Description of returned object.

    """
    parsed_feed.entries = [
        _embedUI_entry(e, s) for e, s in zip(parsed_feed.entries, score)
    ]
    return parsed_feed


_colors = list(Color(hsl=(0.8, 1, 1)).range_to(Color(hsl=(0.8, 1, 0.8)), 256))


def _score2color(score):
    return _colors[min(int(score * 256), 255)].get_hex_l()


def _highlight_text(text, score):
    try:
        sentences = text2sentences(text)
        return u"".join([_highlight_sentence(x, s) for x, s in zip(sentences, score)])
    except Exception:
        log.error(format_exc())
        return text


def _highlight_sentence(sentence, score):
    return _span(
        u"<sup>{s:.2f}</sup> {x}".format(x=sentence, s=score), _score2color(score)
    )


def _best_match_score(x, sentences, score):
    assert len(sentences) == len(score), (len(sentences), len(score))
    return score[np.array([fuzz.ratio(x, s) for s in sentences]).argmax()]


def _highlight_html(html, text, score):
    # this doesn't work yet for paragraphs of multiple sentences
    sentences = text2sentences(text)
    soup = bs.BeautifulSoup(html)
    for x in soup.findAll(text=True):
        x.replaceWith(
            bs.BeautifulSoup(
                _highlight_sentence(x, _best_match_score(x, sentences, score))
            )
        )
    return unicode(soup)
