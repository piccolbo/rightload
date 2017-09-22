from content_extraction import url2text
from InferSent.encoder import models as im
from joblib import Memory
import nltk
from numpy import resize
import os
import re
import torch
from traceback import print_exc
from warnings import warn

memory = Memory(cachedir="feature-cache", verbose=1, bytes_limit = 10**8)
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


@memory.cache(ignore=["entry"])
def url2vec(url, entry=None):
    return text2vec(url2text(url, entry))


def text2sentences(text):
    return sent_detector.tokenize(text.strip())


def text2vec(text, max_sentences=100):
    sentences = text2sentences(text)[:max_sentences]  #limit to cap latency
    infersent.update_vocab(sentences, tokenize=True)
    if sentences:
        return infersent.encode(sentences, tokenize=True)
    else:
        raise FailedExtraction
