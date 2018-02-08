"""Generate a feed in XML from a feedparser parsed feed."""
from datetime import datetime
from feedgenerator import Rss201rev2Feed, Atom1Feed
from functools import reduce  # forward compatibility for Python 3
from time import mktime


def feed2XML(parsed_feed):
    """Take a parsed feed and generates an xml feed."""
    def feedFactory(version):
        if version.upper().find('RSS') != -1:
            return Rss201rev2Feed
        else:
            return Atom1Feed

    pf = parsed_feed.feed
    pf['title'] = pf.get('title', u'')
    pf['link'] = pf.get('link', u'')
    feed = feedFactory(parsed_feed.version)(
        description=pf.get('description', u''),
        **dict(zip(map(str, pf.keys()), pf.values())))
    for e in parsed_feed.entries:
        add_args = _map_entry_structure(_field_map, e)
        if 'published_parsed' in e:
            add_args['pubdate'] = datetime.fromtimestamp(
                mktime(e['published_parsed']))
        if 'updated_parsed' in e:
            add_args['updateddate'] = datetime.fromtimestamp(
                mktime(e['updated_parsed']))
        feed.add_item(**add_args)
    return feed.writeString(parsed_feed.encoding)


# this dict contains an entry for each entry.add_item unicode argument (dates
# are treated separately). Each value is a tuple with a list of paths and a
# default value for the argument. Each path is a tuple of keys used to access
# the nested dict-like structure created by feedparser from the root down. The
# first path to return a trueish value is used, converted to unicode. I've
# found a great variety of fields within the so called RSS and Atom standards.
# This mapping is the result of trial and error and will most likely have to be
# updated to support more feeds.

_field_map = dict(
    title=(['title'], u''),
    link=(['link'], u''),
    description=(
        ["description", ('content', 'value'), "summary"], u''
    ),  # TODO: the correct path is content[0].value doesn't fit my nice scheme
    author_email=([('author_detail', 'email')], None),
    author_name=(['author', ('author_detail', 'name')], None),
    author_link=([('author_link', 'href')], None),
    comments=(None, None),
    unique_id=([("id")], None),
    enclosure=(None, None),
    categories=(None, ()),
    item_copyright=(None, None),
    ttl=(None, None),
    content=(None, None))


def _get_nested(nested_dict, path):
    """Access nested dicts by path.

    Parameters
    ----------
    nested_dict : dict
        A nested dictionary (dict of nested dicts).
    path : collection
        A collection of keys that, applied in order, point to an element in
        a nested dict.

    Returns
    -------
    Any
        An element of the nested dict.

    """
    if isinstance(path, str):
        path = (path, )
    return reduce(lambda x, y: x.get(y, {}), path, nested_dict)


def _map_entry_structure(fmap, entry):
    """Map feed entry element to args for feed.add_item.

    Parameters
    ----------
    fmap : a dict
        Keys are add_item arg names, values describe how to get the value for
        such args out of highly variable feed entries. Specifically they are
        tuples containing different paths, aka collection of keys to use in
        accessing a feed entry nested dict, with priority give to the first
        that points to a trueish value; and a default value when no path points
        to a truish value. When paths is None, we just skip that is we don't
        know how to extract that argument from a feed entry.
    entry : a feedparser feed entry


    Returns
    -------
    type
        Description of returned object.

    """
    return {
        arg: unicode(
            reduce(lambda x, y: x or _get_nested(entry, y) or default, paths,
                   u'') or u'')
        for arg, (paths, default) in fmap.iteritems() if paths is not None
    }
