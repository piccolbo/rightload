from flask import request
import math

def feedbackurl(entry, well_spent):
    return ("http://" + request.host + "/learn/" +
            ("l" if well_spent else "d") + "/" + entry.link)


def is_long(text):
    return len(text) > 1000

def sigmoid(x):
    return 1/(1+ math.exp(-x))

def embedUI_entry(entry, score):
    bar = ('<p style="BACKGROUND-COLOR: #BBD9EE">' + (
        '<a href="{well_spent_link}" target="_top"><font color="green">Time Well Spent</font></a>'
        if score < 0 else
        '<a href="{wasted_link}" target="_top"><font color="red">Time Wasted</font></a>'
    ) + '</p>').format(
        well_spent_link=feedbackurl(entry=entry, well_spent=True),
        wasted_link=feedbackurl(entry=entry, well_spent=False))
    desc = entry.get('description', '')
    entry['description'] = bar + desc + (bar if is_long(desc) else '')
    if entry.has_key('content'):
        content = entry['content'][0].value
        entry['content'][0].value = bar + content + (bar if len(content) > 1000\
                                                     else '')
    if entry.has_key('title'):
        entry['title'] = u"{sigscore:.2f} |{score:.2f} | {title}".format(
            sigscore=sigmoid(score), score = score, title=entry['title'])
    return entry


def embedUI(parsed_feed, score):
    parsed_feed.entries = [
        embedUI_entry(e, s) for e, s in zip(parsed_feed.entries, score)
    ]
    return parsed_feed
