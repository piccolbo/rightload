from goose import Goose
import nltk
import os
import torch
from InferSent.encoder import models

sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

infersent = torch.load(
    'InferSent/encoder/infersent.allnli.pickle',
    map_location=lambda storage, loc: storage)
infersent.use_cuda = False
infersent.set_glove_path('InferSent/dataset/GloVe/glove.840B.300d.txt')
g = Goose()

#TODO: memoize to avoid repeat computation
def url2vec(url):
    article = g.extract(url=url)
    text = article.title + "\n" + article.cleaned_text
    sentences = sent_detector.tokenize(text.strip())
    infersent.build_vocab(sentences, tokenize=True)
    return infersent.encode(sentences, tokenize=True).max(axis=0)
