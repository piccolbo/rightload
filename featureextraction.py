from InferSent.encoder import models as im
from goose import Goose
from goose.article import Article
import nltk
from numpy import resize
import os
import requests
import shove
import torch
from warnings import warn

feature_store = shove.Shove("simple://")
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
infersent.build_vocab_k_words(K=100000)

g = Goose(dict(enable_image_fetching=False))


class FailedExtraction(Exception):
    pass


def entry2vec(entry):
    vec = feature_store.get(entry.link)
    if vec is None:
        vec = text2vec(*entry2text(entry))
        feature_store[entry.link] = vec
    return vec


def url2vec(url):
    vec = feature_store.get(url)
    return vec if vec is not None else text2vec(*url2text(url))


def url2text(url):
    try:
        article = g.extract(url=url)
    except:
        try:
            article = g.extract(raw_html=requests.get(url).content)
        except:
            article = Article()
    return article.title, article.cleaned_text


def entry2text(entry):
    title, body = url2text(entry.link)
    return title or entry.title, body or g.extract(
        raw_html=entry.summary).cleaned_text


def text2vec(title, body):
    text = title + "\n" + body
    sentences = sent_detector.tokenize(
        text.strip())[:50]  #limit to cap latency
    # infersent.build_vocab(sentences, tokenize=True)
    if sentences:
        return infersent.encode(sentences, tokenize=True).max(axis=0)
    else:
        raise FailedExtraction
