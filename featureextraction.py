import BeautifulSoup as bs
from InferSent.encoder import models as im
from goose import Goose
from goose.article import Article
import nltk
from numpy import resize
import os
import re
import requests
import torch
from warnings import warn

sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

#alternate infersent load method based on https://stackoverflow.com/questions/42703500/best-way-to-save-a-trained-model-in-pytorch as chdir doesn't work in flask
config = dict(
    bsize=64,
    word_emb_dim=300,
    enc_lstm_dim=2048,
    pool_type='max',
    dpout_model=0.0,
    use_cuda=False)
# copied from loaded object
infersent = im.BLSTMEncoder(config)
infersent.load_state_dict(
    torch.load(
        'InferSent/encoder/infersent.allnli.state.pickle',
        map_location=lambda storage, loc: storage))
#saved with torch.save(infersent.state_dict(), "InferSent/encoder/infersent.allnli.state.pickle")
infersent.set_glove_path('InferSent/dataset/GloVe/glove.840B.300d.txt')
infersent.build_vocab_k_words(K=1)

g = Goose(dict(enable_image_fetching=False))


class FailedExtraction(Exception):
    pass


def url2vec(url, feature_db, entry=None):
    if feature_db.get(url) is not None:
        return feature_db[url]
    else:
        print("Feat extraction: {url}".format(url=url))
        try:
            retval = text2vec(url2text(url))
        except:
            warn(
                "Can't extract from entry.link. Falling back to entry content")
            if entry is not None:
                retval = text2vec(entry2text(entry))
            else:
                raise
        feature_db[url] = retval
        feature_db.sync()
        return retval


def goose_extract(**kwargs):
    article = g.extract(**kwargs)
    text = article.title + "\n" + article.cleaned_text
    if len(text) < 200:
        raise FailedExtraction
    else:
        return text


def soup_extract(raw_html):
    soup = bs.BeautifulSoup(
        raw_html, convertEntities=bs.BeautifulSoup.ALL_ENTITIES)
    return " ".join([
        x for x in soup.findAll(text=True)
        if x.parent.name not in
        ['style', 'script', 'head', 'title', 'meta', '[document]']
        and len(x) > 1
    ])


def url2text(url):
    try:
        text = goose_extract(url=url)
    except:
        try:
            raw_html = requests.get(url).content
            text = goose_extract(raw_html=raw_html)
        except:
            text = soup_extract(raw_html)
            if len(text) < 40:
                raise FailedExtraction
    return text


def entry2text(entry):
    try:
        return url2text(entry.link)
    except:
        return entry.title + ". " + g.extract(
            raw_html=entry.summary).cleaned_text


def text2vec(text):
    sentences = sent_detector.tokenize(
        text.strip())[:100]  #limit to cap latency
    infersent.update_vocab(sentences, tokenize=True)
    if sentences:
        return infersent.encode(sentences, tokenize=True)
    else:
        raise FailedExtraction
