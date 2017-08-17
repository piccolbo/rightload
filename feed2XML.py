import feedgenerator
import re
from datetime import datetime
from time import mktime


def feed2XML(parsed_feed):
    "takes a parsed feed and generates an xml feed"

    def feedFactory(version):
        if version.upper().find("RSS") != -1:
            return feedgenerator.Rss201rev2Feed
        else:
            return feedgenerator.Atom1Feed

    pf = parsed_feed.feed
    pf['title'] = pf.get('title', '')
    pf['link'] = pf.get('link', '')
    feed = feedFactory(parsed_feed.version)(
        description=pf.get('description', ''),
        **dict(zip(map(str, pf.keys()), pf.values())))
    for e in parsed_feed.entries:
        e['title'] = e.get('title', '')
        e['link'] = e.get('link', '')
        if e.has_key('author'):
            e['author_name'] = e['author']
        if e.has_key('author_detail'):
            if e['author_detail'].has_key('name'):
                e['author_name'] = e['author_detail']['name']
            if e['author_detail'].has_key('email'):
                e['author_email'] = e['author_detail']['email']
            if e['author_detail'].has_key('href'):
                e['author_link'] = e['author_detail']['href']
        if e.has_key('id'):
            e['unique_id'] = e['id']
        if e.has_key('published_parsed'):
            e['pubdate'] = datetime.fromtimestamp(
                mktime(e['published_parsed']))
        if e.has_key('updated_parsed'):
            e['pubdate'] = datetime.fromtimestamp(mktime(e['updated_parsed']))
        feed.add_item(
            description=e.get('description', ''),
            **dict(zip(map(str, e.keys()), e.values())))
    return feed.writeString(parsed_feed.encoding)
