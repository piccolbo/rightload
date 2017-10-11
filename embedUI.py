import BeautifulSoup as bs
from content_extraction import url2text, url2html
from colour import Color
from debug import spy
from feature_extraction import text2sentences
from flask import request
from fuzzywuzzy import fuzz
import logging as log
import numpy as np
import re
from traceback import format_exc


def _feedbackurl(link, well_spent):
    return (u"http://" + request.host + u"/feedback/" +
            (u"l" if well_spent else u"d") + u"/" + link)


def _is_long(text):
    return len(text) > 1000


def _p(style, text):
    return u'<p style="{style}">{text}</p>'.format(style=style, text=text)


def _a(href, target, text):
    return u'<a href="{href}" target="{target}">{text}</a>'.format(
        href=href, target=target, text=text)


def _font(color, text):
    return u'<font color="{color}">{text}</font>'.format(
        color=color, text=text)


def _span(text, color):
    style1 = u'"border-bottom: 3px solid {color}"'
    style2 = u'"text-decoration: underline; text-decoration-color: {color}"'
    style = style1.format(color=color)
    return u'<span style={style}>{text}</span>'.format(text=text, style=style)


def _feedback_link(is_good, entry_link):
    return _a(
        href=_feedbackurl(link=entry_link, well_spent=is_good),
        target=u"_top",
        text=_font(
            color=u"green" if is_good else u"red",
            text=u"Time Well Spent" if is_good else u"Time Wasted"))


def _conditional_bar(mean_score, entry_link):
    return _p(
        style=u"BACKGROUND-COLOR: #DBDBDB",
        text=(_feedback_link(True, entry_link) if mean_score <= 0.5 else u'')
        + (u" or " if mean_score == 0.5 else u"")
        + (_feedback_link(False, entry_link) if mean_score >= 0.5 else u''))


# def _bar(entry_link):
#     return _p(
#         style=u"BACKGROUND-COLOR: #DBDBDB",
#         text=_feedback_link(True, entry_link) + u" or " + _feedback_link(
#             False, entry_link))


def _add_bar(text, mean_score, entry_link):
    bar = _conditional_bar(mean_score, entry_link)
    return bar + text + (bar if _is_long(text) else u'')


def _embedUI_entry(entry, score):
    mean_score = score.mean()
    text = url2text(entry.link, entry)
    high_text = _highlight_text(text, score)
    # html = url2html(entry.link, entry)
    # high_html = _highlight_html(html, text, score)
    if u'description' in entry:
        entry[u'description'] = _add_bar(high_text, mean_score, entry.link)
    if u'content' in entry:
        entry[u'content'][0].value = _add_bar(high_text, mean_score,
                                              entry.link)
        entry[u'content'][0].value = _add_bar(high_text, mean_score,
                                              entry.link)
    if u'title' in entry:
        entry[u'title'] = u"{mean_score:} | {title}".format(
            mean_score=int(mean_score * 100), title=entry[u'title'])
    return entry


def embedUI(parsed_feed, score):
    parsed_feed.entries = [
        _embedUI_entry(e, s) for e, s in zip(parsed_feed.entries, score)
    ]
    return parsed_feed


_colors = list(
    Color(hsl=(0.16, 1, 1)).range_to(Color(hsl=(0.16, 1, 0.5)), 256))


def _score2color(score):
    return _colors[int(score * 256)].get_hex_l()


def _highlight_text(text, score):
    try:
        sentences = text2sentences(text)
        return u"".join(
            [_highlight_sentence(x, s) for x, s in zip(sentences, score)])
    except Exception:
        log.error(format_exc())
        return text


def _highlight_sentence(sentence, score):
    return _span(u"<sup>{s:.2f}</sup>{x}".format(x=sentence, s=score),
                 _score2color(score))


def _best_match_score(x, sentences, score):
    return score[np.array([fuzz.ratio(x, s) for x in sentences]).argmax()]


def _highlight_html(html, text, score):
    sentences = text2sentences(text)
    soup = bs.BeautifulSoup(html)
    for x in soup.findAll(text=True):
        x.replaceWith(
            bs.BeautifulSoup(
                _highlight_sentence(x, _best_match_score(x, sentences,
                                                         score))))
    return str(soup)


def _escape(s):
    return re.sub(r"[(){}\[\].*?|^$\\+-]", r"\\\g<0>", s)


def _patternize(sentence):
    return re.sub('(\s)+', '.*', _escape(sentence))
