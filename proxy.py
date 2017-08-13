import copy
import feedcache
from flask import request, Response
from ml import score_feed
import shove


store = shove.Shove("simple://")


def proxy(url):
    if request.method == 'GET':
        # process url
        # get content
        fc = feedcache.Cache(store)  #defaul timetolive = 300
        url = "http://" + url
        parsed_feed = fc.fetch(
            url, offline=True) or fc.fetch(
                url)  #defaults: force_update = False, offline = False

        #return content
        status = parsed_feed.get('status', 404)
        if status >= 400:  #deal with errors
            response = ("External error", status, {})
        elif status >= 300:  #deal with redirects
            response = ("", status,
                        dict(Location="feed/{url}".format(url=url)))
        else:
            etag = request.headers.get('IF_NONE_MATCH')
            modified = request.headers.get('IF_MODIFIED_SINCE')
            if (etag and etag == parsed_feed.get('etag')) or (
                    modified and modified == parsed_feed.get('modified')):
                response = ("", 304, {})
            else:
                if not parsed_feed['bozo']:
                    parsed_feed = copy.deepcopy(
                        parsed_feed
                    )  #if it's bozo copy fails and copy is not cached, so we skip
                    # deepcopy needed to avoid side effects on cache
                response = (process(
                    parsed_feed, ), 200, {})
        if parsed_feed.has_key('headers'):  #some header rinsing
            for k, v in parsed_feed.headers.iteritems():
                # TODO: seems to work with all the hop by hop  headers unset or to default values, need to look into this
                if not is_hop_by_hop(
                        k
                ) and k != 'content-length' and k != 'content-encoding':
                    # let django deal with these headers
                    response[2][k] = v
        return response
    else:
        return ("POST not allowed for feeds", 405, {})


def process(parsed_feed):
    if (len(parsed_feed.entries) > 0):
        score = score_feed(parsed_feed)
        embedUI(parsed_feed, filter_info, [
            e for (e, (serve, s, p)) in zip(entries, filter_info) if serve
        ])
    return feedgen(parsed_feed)
