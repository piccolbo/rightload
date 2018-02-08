"""Data persistence layer for rightload."""
from flask import g
from os.path import basename
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
    attr_name = '_' + basename(path)
    db = getattr(g, attr_name, None)
    if db is None:
        db = shove.Shove('lite://' + path)
        setattr(g, attr_name, db)
    return db


def feed_db():
    """Access feed db.

    Returns
    -------
    Shove object
        A Shove object with feed urls as keys and feed content as values.

    """
    return _get_shove_db('feed.sqlite')


def training_db():
    """Access for training db.

    Returns
    -------
    Shove object
        Shove object with urls as keys and feedback info as values.

    """
    return _get_shove_db('training.sqlite')


def model_db():
    """Access for model db.

    Returns
    -------
    Shove object
        Shove object with a single key and value a sklearn model.

    """
    return _get_shove_db('model.sqlite')
