from feedbackurl import feedbackurl
from flask import request

def feedbackurl(entry, like):
    return ("http://" + request.host + "/learn/" + ( "l" if like else "d") + "/" + entry.link)

def embedUI_entry(entry, score):
    bar = ('<p style="BACKGROUND-COLOR: #BBD9EE">' + (
        '<a href="{like_link}" target="_top"><font color="green">like</font></a>'
        if not is_good else
        '<a href="{ dislike_link }" target="_top"><font color="red">dislike</font></a>'
    ) + '</p>').format(
        like_link=feedbackurl(entry=entry, like=True),
        dislike_link=feedbackurl(entry=entry, like=False))
    entry['description'] = bar + entry.get('description', '') + bar
    if entry.has_key('content'):
        entry['content'][0].value = bar + entry['content'][0].value + bar
    if entry.has_key('title'):
        entry['title'] = ('* ' if score >= 0 else '? ') + entry['title']
    return entry


def embedUI(parsed_feed, score):
    parsed_feed.entries = [
        embedUI_helper(e, s) for e, s in zip(parsed_feed.entries, score)
    ]
