from flask import request
import math


def feedbackurl(link, well_spent):
    return ("http://" + request.host + "/feedback/" +
            ("l" if well_spent else "d") + "/" + link)


def is_long(text):
    return len(text) > 1000


# def sigmoid(x):
#     return 1 / (1 + math.exp(-x))


def p(style, text):
    return '<p style="{style}">{text}</p>'.format(style=style, text=text)


def a(href, target, text):
    return '<a href="{href}" target="{target}">{text}</a>'.format(
        href=href, target=target, text=text)


def font(color, text):
    return '<font color="{color}">{text}</font>'.format(color=color, text=text)

def embedUI_entry(entry, score):
    link = entry.link
    good_link = a(
        href=feedbackurl(link=link, well_spent=True),
        target="_top",
        text=font(color="green", text="Time Well Spent"))
    bad_link = a(
        href=feedbackurl(link=link, well_spent=False),
        target="_top",
        text=font(color="red", text="Time Wasted"))
    bar = p(
        style="BACKGROUND-COLOR: #DBDBDB",
        text=(good_link if score <= 0.5 else '') + \
            (" or " if score == 0.5 else "") + \
            (bad_link if score >= 0.5 else ''))
    desc = entry.get('description', '')
    entry['description'] = bar + desc + (bar if is_long(desc) else '')
    if entry.has_key('content'):
        content = entry['content'][0].value
        entry['content'][0].value = bar + content + (bar if len(content) > 1000\
                                                     else '')
    if entry.has_key('title'):
        entry['title'] = u"{score:} | {title}".format(
            score=int(score * 100), title=entry['title'])
    return entry


def embedUI(parsed_feed, score):
    parsed_feed.entries = [
        embedUI_entry(e, s) for e, s in zip(parsed_feed.entries, score)
    ]
    return parsed_feed
