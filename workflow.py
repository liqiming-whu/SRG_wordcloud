#!/usr/bin/env python3
import os
import re
import csv
import time
import json
from functools import wraps
from collections import Counter
import matplotlib.pyplot as plt
from pubmed import Search_Pubmed
from text_utils import process_text, process_word_freq
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords as StopWords
from nltk.probability import FreqDist
from wordcloud import WordCloud
from word_svg import SVG
from multiprocessing import Pool as ThreadPool


class LogFile:
    def __init__(self, path):
        self.path = path
        self.file = open(path, "a", encoding="utf-8")
        localtime = time.asctime(time.localtime(time.time()))
        self.log("=================================\nStart log: {}\n".format(localtime))

    def __str__(self):
        return "logfile {}".format(self.path)

    __repr__ = __str__

    def log(self, content):
        print(content.rstrip())
        self.file.write(content)

    def close(self):
        self.file.close()


class Fetch:
    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists("log"):
            os.mkdir("log")
        logpath = os.path.join("log", "{}_results.log".format(filename))
        logfile = LogFile(logpath)
        self.logfile = logfile
        self.stopwords = self.stopwords()

    def __str__(self):
        return "Fetch {}".format(self.query)

    __repr__ = __str__

    @staticmethod
    def stopwords():
        stopwords_path = os.path.join('data', 'stopwords.txt')
        sup_stopwords_path = os.path.join('data', 'supplementary_stopwords.txt')
        stopwords = set(open(stopwords_path).read().split())
        add = set(open(sup_stopwords_path).read().split())
        stopwords = stopwords | add | set(StopWords.words('english'))

        return stopwords

    @staticmethod
    def parse_search_items():
        species_path = os.path.join("data", "species.csv")
        with open(species_path) as f:
            for line in f:
                fileds = line.rstrip().split(",")
                name, alias = fileds[0], fileds[1]
                query = "{} OR {} AND sex reversal".format(name, alias)
                file_name = name.replace(" ", "_")
                yield query, file_name

    @property
    def query_dict(self):
        q = dict()
        for query, file_name in self.parse_search_items():
            q[file_name] = query

        return q

    def exec(type):
        def exec_decorater(func):
            @wraps(func)
            def wrapped_func(self):
                path = Fetch.fetch_path(self.filename, type=type)
                if not os.path.exists(path):
                    return func(self)
                elif os.path.getsize(path) == 0:
                    return func(self)
                else:
                    return os.path.getsize(path)
            return wrapped_func
        return exec_decorater

    @exec(type='info')
    def search(self):
        if not os.path.exists("results"):
            os.mkdir("results")
        outdir = os.path.join("results", self.filename)
        query = self.query_dict[self.filename]
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        search_results = Search_Pubmed(query)
        count = int(search_results.count)
        self.logfile.log("Query: {}, Count: {}.\n".format(query, count))
        if count > 10:
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            csvfile = os.path.join(outdir, self.filename+"_info.csv")
            search_results.save_info(csvfile)

        return count

    def path(self, type=None):
        if type == "info":
            return os.path.join("results", self.filename, "{}_info.csv".format(self.filename))
        if type == "fulltext":
            return os.path.join("results", self.filename, "{}_full.txt".format(self.filename))
        if type == "freq":
            return os.path.join("results", self.filename, "{}_words_freq.json".format(self.filename))
        if type == "pdf":
            return os.path.join("results", self.filename, "{}.pdf".format(self.filename))
        if type == "svg":
            return os.path.join("results", self.filename, "{}.svg".format(self.filename))
        if type == "articles":
            return os.path.join("results", self.filename, "artciles")

        return os.path.join("results", self.filename)

    @staticmethod
    def fetch_path(filename, type=None):
        if type == "info":
            return os.path.join("results", filename, "{}_info.csv".format(filename))
        if type == "fulltext":
            return os.path.join("results", filename, "{}_full.txt".format(filename))
        if type == "freq":
            return os.path.join("results", filename, "{}_words_freq.json".format(filename))
        if type == "pdf":
            return os.path.join("results", filename, "{}.pdf".format(filename))
        if type == "svg":
            return os.path.join("results", filename, "{}.svg".format(filename))
        if type == "all":
            return os.path.join("results", "all.pdf")

        return os.path.join("results", filename)

    @staticmethod
    def parse_source(source):
        fileds = source.split("doi:")
        journal = fileds[0].strip()
        doi = fileds[1].split()[0].rstrip(".")

        return journal, doi

    @exec(type="fulltext")
    def get_full_text(self):
        info = open(self.path(type="info"))
        reader = csv.reader(info)
        full_text_path = self.path(type="fulltext")
        article_apth = self.path(type="articles")
        if not os.path.exists(article_apth):
            os.mkdir(article_apth)
        from full_text import Article
        with open(full_text_path, "w", encoding="utf-8") as f:
            next(reader)
            for row in reader:
                pmid = row[0]
                source = row[3]
                arti_path = os.path.join(article_apth, "{}.txt".format(pmid))
                if os.path.exists(arti_path) and os.path.getsize(arti_path) > 500:
                    continue
                elif os.path.exists(arti_path):
                    os.unlink(arti_path)
                try:
                    _, doi = self.parse_source(source)
                except Exception:
                    self.logfile.log("Article {} doi not found.\n".format(pmid))
                    continue
                try:
                    page = Article(pmid, doi, self.logfile)
                except Exception:
                    self.logfile.log("Article {} connect failed.\n".format(pmid))
                    continue
                page_text = page.get_text()
                if page_text:
                    with open(arti_path, "w", encoding="utf-8") as p:
                        p.write(page_text)
            file_list = os.listdir(article_apth)
            for filename in file_list:
                f.write(open(os.path.join(article_apth, filename), encoding='utf-8').read())
        self.logfile.log("{} articles have been saved.\n".format(len(file_list)))
        Article.browser.quit()

    @staticmethod
    def dict_filter(word_freq, stopwords):
        word_freq = dict(word_freq.most_common(20000))
        word_f = dict()
        for word, count in word_freq.items():
            if len(word.split("_")) > 2:
                continue
            if len(word.split("-")) > 2:
                continue
            if word in stopwords:
                continue
            if re.match(r'\d+', word):
                continue
            if re.match(r'[+-/?.,]$', word):
                continue
            if re.match(r'\S+\.$', word):
                continue
            word_f[word] = count
        return Counter(word_f)

    @exec(type="freq")
    def save_word_freq(self):
        text_path = self.path(type='fulltext')
        text = open(text_path, encoding="utf-8").read()
        words = word_tokenize(process_text(text))
        word_freq = FreqDist(words)
        filtered_word_freq = process_word_freq(Fetch.dict_filter(word_freq, self.stopwords), self.filename)

        word_freq_path = self.path(type="freq")
        with open(word_freq_path, "w", encoding="utf-8") as f:
            json.dump(filtered_word_freq, f)
        word_path = self.path()
        with open(os.path.join(word_path, "word_freq.txt"), "w", encoding="utf-8") as f:
            for key, value in filtered_word_freq.items():
                f.write("{}\n".format(key))

    def generate_freq(self):
        word_freq_path = self.path(type="freq")
        word_freq = process_word_freq(None, self.filename)
        if word_freq:
            with open(word_freq_path, "w", encoding="utf-8") as f:
                json.dump(word_freq, f)


    @exec(type="svg")
    def wordcloud(self):
        if not os.path.exists(self.path(type="freq")):
            return
        word_freq = json.load(open(self.path(type="freq")))
        wordcloud_path = self.path(type="pdf")
        svg_path = self.path(type="svg")
        wordcloud = WordCloud(background_color="white", scale=3,
                              width=600, height=400, margin=2).generate_from_frequencies(word_freq)
        plt.axis('off')
        plt.imshow(wordcloud)
        plt.show()
        plt.close()
        wordcloud.to_file(wordcloud_path)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(wordcloud.to_svg())
    
    def word_source(self):
        source_dir = os.path.join(self.path(), "word_source")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        freq = json.load(open(self.path(type="freq"))).keys()
        article_dir = self.path(type="articles")
        detail = csv.reader(open(self.path(type="info")))
        next(detail)
        detail_dict = dict()
        for row in detail:
            detail_dict[row[0]] = row
        for word in freq:
            source_p = os.path.join(source_dir, word.replace(" ", "_").replace("/", "_")+".csv")
            source_f = open(source_p, "w", newline="", encoding="utf-8")
            csvf = csv.writer(source_f)
            csvf.writerow(["Pubmed_ID", "Title", "Author", "Source", "Abstract"])
            for art in os.listdir(article_dir):
                pmid = art.rstrip(".txt")
                art_p = os.path.join(article_dir, art)
                if word in open(art_p, encoding="utf-8").read():
                    csvf.writerow(detail_dict[pmid])
            source_f.close()

    def run(self):
        self.logfile.log("Start fetch {}...\n".format(self.filename))
        count = self.search()
        if count >= 10:
            self.get_full_text()
            self.logfile.close()
            self.save_word_freq()
            self.wordcloud()
            self.word_source()
        else:
            self.generate_freq()
            self.wordcloud()
        self.logfile.close()

    @staticmethod
    def run_all(filename_list):
        word_freq = Counter()
        for filename in filename_list:
            freq_path = Fetch.fetch_path(filename, type="freq")
            if os.path.exists(freq_path):
                word_freq += Counter(json.load(open(freq_path)))

        filtered_word_freq = process_word_freq(Fetch.dict_filter(word_freq, Fetch.stopwords()), self.filename)
        wordcloud_path = os.path.join("results", "all.pdf")
        svg_path = os.path.join("results", "all.svg")
        word_path = os.path.join("results", "words.txt")
        with open(word_path, "w") as f:
            f.write("\n".join(filtered_word_freq.keys()))
        wordcloud = WordCloud(background_color="white", scale=3,
                              collocations=True, width=600,
                              height=400, margin=2).generate_from_frequencies(filtered_word_freq)
        plt.axis('off')
        plt.imshow(wordcloud)
        plt.show()
        plt.close()
        wordcloud.to_file(wordcloud_path)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(wordcloud.to_svg())

    @staticmethod
    def run_freq(filename_list):
        freq = open(os.path.join("results", "freq_list.tsv"), "w", encoding='utf-8')
        freq.write("Symbol\tSpecies\tNumber\tRGB\tSex\n")
        for filename in filename_list:
            word_freq_path = os.path.join("results", "freq_tsv", filename+".tsv")
            if not os.path.exists(word_freq_path):
                continue
            svg = SVG(os.path.join("results", filename, filename+".svg"))
            whitelist_dir = os.path.join("data", "whitelist_species", filename)
            male = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, "male.txt"))]
            female = male = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, "female.txt"))]
            word_rgb = svg.to_dict(male, female)
            species = filename.replace("_", " ")
            with open(word_freq_path) as f:
                for line in f:
                    fileds = line.split("\t")
                    symbol = fileds[0]
                    number = fileds[1]
                    rgb = word_rgb[symbol]
                    sex = fileds[2].rstrip()
                    freq.write("{}\t{}\t{}\t{}\t{}\n".format(symbol, species, number, rgb, sex))

        freq.close()


def run_fetch(filename):
    fetch = Fetch(filename)
    fetch.run()


if __name__ == "__main__":
    items = list(Fetch.parse_search_items())
    filenames = [name[1] for name in items]

    # args_lst = [filenames[i:i+4] for i in range(0, len(filenames), 4)]
    # threads_lst = []
    # for lst in args_lst:
    #     pool = ThreadPool()
    #     pool.map(run_fetch, lst)
    #     pool.close()
    #     pool.join()

    for filename in filenames:
        run_fetch(filename)
    # Fetch.run_all(filenames)

    # run_fetch("Danio_rerio")
    # Fetch.run_all(filenames)
    Fetch.run_freq(filenames)
