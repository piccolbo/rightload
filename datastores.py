from flask import g
from os.path import basename
import shove


def _get_shove_db(path):
    attr_name = '_' + basename(path)
    db = getattr(g, attr_name, None)
    if db is None:
        db = shove.Shove('lite://' + path)
        setattr(g, attr_name, db)
    return db


def training_db():
    return _get_shove_db('training.sqlite')


def model_db():
    return _get_shove_db('model.sqlite')
