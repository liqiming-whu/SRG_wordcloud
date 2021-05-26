#!/usr/bin/env python3
import os
import json
from workflow import Fetch
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from text_utils import process_text, GENES, DRUGS


def process_freq_dict(freq_dict, filename, num):
    species_stopwords = os.path.join("data", "stopwords_species", filename+".txt")
    if os.path.exists(species_stopwords):
        StopWords = open(species_stopwords).read().split("\n")
        freq_dict = dict(i for i in freq_dict.items() if i[0] not in StopWords)
    whitelist_dir = os.path.join("test_srg", "test_zebrafish")

    freq = list(freq_dict.items())
    male = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, f"male_{num}.txt"))]
    female = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, f"female_{num}.txt"))]
    add = [(i, 1) for i in male+female if i not in freq_dict.keys()]
    freq = freq + add
    freq_tsv_dir = os.path.join("test_srg", "freq_tsv")
    if not os.path.exists(freq_tsv_dir):
        os.mkdir(freq_tsv_dir)
    freq_tsv = os.path.join(freq_tsv_dir, filename+".tsv")

    with open(freq_tsv, "w", encoding="utf-8") as f:
        for word, count in freq:
            if word in male:
                f.write("{}\t{}\tmale\n".format(word, count))
            elif word in female:
                f.write("{}\t{}\tfemale\n".format(word, count))
            else:
                f.write("{}\t{}\tNA\n".format(word, count))
    return dict(freq)


def process_word_freq(word_freq, filename, num):
    print("word_freq length: ", len(word_freq))
    uniq = Counter(word.lower() for word in word_freq)
    duplicate = [word for word, freq in uniq.items() if freq > 1]
    remove = Counter()
    add = Counter()
    for word in duplicate:
        freq = 0
        order = 0
        for key in word_freq.keys():
            if key.lower() == word:
                order += 1
                if order == 1:
                    add_key = key
                freq += word_freq[key]
                remove[key] = word_freq[key]
        add[add_key] = freq
    word_freq = word_freq - remove + add
    high_frep = word_freq.most_common(200)
    low_freq = [(key, value) for (key, value) in word_freq.most_common() if (key, value) not in high_frep]
    genes_drugs = [(word, freq) for (word, freq) in low_freq if word in GENES or word in DRUGS]
    freq = word_freq.most_common(200 - len(genes_drugs)) + genes_drugs

    freq_dict = dict((word.replace("_", " "), count) for word, count in freq)

    return process_freq_dict(freq_dict, filename, num)


class TestFetch(Fetch):
    def test_save_word_freq(self, name, num):
        text_path = self.path(type='fulltext')
        text = open(text_path, encoding="utf-8").read()
        words = word_tokenize(process_text(text))
        word_freq = FreqDist(words)
        filtered_word_freq = process_word_freq(Fetch.dict_filter(word_freq, self.stopwords), self.filename, num)

        word_freq_path = os.path.join("test_srg", name)
        with open(word_freq_path, "w", encoding="utf-8") as f:
            json.dump(filtered_word_freq, f)

    def test_word_source(self, name):
        freq = json.load(open(os.path.join("test_srg", name))).keys()

        items = list(Fetch.parse_search_items())
        filenames = [name[1] for name in items]

        pubmed_list = []
        for word in freq:
            for filename in filenames:
                article_dir = os.path.join("results", filename, "articles")
                if not os.path.exists(article_dir):
                    continue
                for art in os.listdir(article_dir):
                    pmid = art.rstrip(".txt")
                    art_p = os.path.join(article_dir, art)
                    if word in open(art_p, encoding="utf-8").read():
                        pubmed_list.append(pmid)
        articles_num = len(set(pubmed_list))

        print(f"Collected {articles_num} articles")


if __name__ == "__main__":
    for i in ('50', '100', '150', '200'):
        test = TestFetch("Danio_rerio")
        test.test_save_word_freq(f"zebrafish_{i}.json", i)
        test.test_word_source(f"zebrafish_{i}.json")
