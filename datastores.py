from flask import g
from os.path import basename
import shove



def get_shove_db(path):
    db = getattr(g, '_' + basename(path), None)
    if db is None:
        db = g._database = shove.Shove('lite://' + path)
    return db

def classifier_db():
    return get_shove_db('classifier.sqlite')


def training_db():
    return get_shove_db('training.sqlite')





# tear down example
# I think shove is smart enough

# @app.teardown_appcontext
# def close_connection(exception):
#     db = getattr(g, '_database', None)
#     if db is not None:
#         db.close()
