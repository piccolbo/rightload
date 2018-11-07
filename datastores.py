"""Data persistence layer for rightload."""
from flask import g
from os.path import basename, getmtime
import shove


def _get_shove_db(path):
    """Get or create a sqlite-backed shove db.

    Parameters
    ----------
    path : string
        Path to sqlite db, opened or created as needed.

    Returns
    -------
    Shove object
        A dict-like object backed by the db at path, attached to flask context.

    """
    attr_name = "_" + basename(path)
    db = getattr(g, attr_name, None)
    if db is None:
        db = shove.Shove("lite://" + path)
        setattr(g, attr_name, db)
    return db


def get_model_db_unix_time():
    # using private API, fix
    fname = model_db()._store._engine
    return getmtime(fname)


def feed_db():
    """Access feed db.

    This is just a cache for feed processing, only for performance and to be nice on the web servers.

    Returns
    -------
    Shove object
        A Shove object with feed urls as keys and feed content as values.

    """
    return _get_shove_db("feed.sqlite")


def training_db():
    """Access training db.

    This has the user feedback as (url, feedback) pairs.

    Returns
    -------
    Shove object
        Shove object with urls as keys and feedback info as values.

    """
    return _get_shove_db("training.sqlite")


def model_db():
    """Access for model db.

    This stores the learning model.

    Returns
    -------
    Shove object
        Shove object with a single key and value a sklearn model.

    """
    return _get_shove_db("model.sqlite")
