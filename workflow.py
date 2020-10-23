#!/usr/bin/env python3
import os
import csv
import time
import json
from functools import wraps
from pubmed import Search_Pubmed
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords as StopWords
from nltk.probability import FreqDist
from wordcloud import WordCloud
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
        stopwords_path = os.path.jon('data', 'stopwords.txt')
        sup_stopwords_path = os.path.join('data', 'supplementary_stopwords.txt')
        stopwords = set(line.rstrip() for line in open(stopwords_path))
        add = set(line.rstrip() for line in open(sup_stopwords_path))
        stopwords = stopwords | add | set(StopWords.words('english'))

        return stopwords

    @staticmethod
    def parse_search_items():
        with open("species.csv") as f:
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
        if count:
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
                    continue
                    self.logfile.log("Article {} doi not found.")
                page = Article(pmid, doi, self.logfile)
                page_text = page.get_text()
                if page_text:
                    with open(arti_path, "w", encoding="utf-8") as p:
                        p.write(page_text)
            file_list = os.listdir(article_apth)
            for filename in file_list:
                f.write(open(os.path.join(article_apth, filename)).read())
        self.logfile.log("{} articles have been saved.\n".format(len(file_list)))
        Article.browser.quit()

    @staticmethod
    def dict_filter(word_freq, stopwords):
        return dict((word.capitalize(), word_freq[word]) for word in word_freq if word not in stopwords)

    @exec(type="freq")
    def save_word_freq(self):
        text_path = self.path(type='fulltext')
        text = open(text_path, encoding="utf-8").read().lower()
        words = word_tokenize(text)
        word_freq = FreqDist(words)
        filtered_word_freq = Fetch.dict_filter(word_freq, self.stopwords)
        word_freq_path = self.path(type="freq")
        with open(word_freq_path, "w", encoding="utf-8") as f:
            json.dump(filtered_word_freq, f)

    @exec(type="pdf")
    def wordcloud(self):
        word_freq = json.load(open(self.path(type="freq")))
        wordcloud_path = self.path(type="pdf")
        wordcloud = WordCloud(background_color="white",
                              stopwords=self.stopwords, scale=3,
                              collocations=False, width=1000,
                              height=750, margin=2).generate_from_frequencies(word_freq)
        wordcloud.to_file(wordcloud_path)

    def run(self):
        self.logfile.log("Start fetch {}...\n".format(self.filename))
        count = self.search()
        if count:
            self.get_full_text()
            self.logfile.close()
            self.save_word_freq()
            self.wordcloud()
        self.logfile.close()

    @staticmethod
    def run_all(filename_list):
        text = ""
        for filename in filename_list:
            text_path = Fetch.fetch_path(filename, type="fulltext")
            try:
                text += open(text_path).read().lower()
            except Exception:
                continue
        words = word_tokenize(text)
        word_freq = FreqDist(words)
        filtered_word_freq = Fetch.dict_filter(word_freq, Fetch.stopwords())
        wordcloud_path = os.path.join("results", "all.pdf")
        word_path = os.path.join("results", "words.txt")
        with open(word_path, "w") as f:
            f.write("\n".join(filtered_word_freq.keys()))
        wordcloud = WordCloud(background_color="white",
                              stopwords=Fetch.stopwords(), scale=2,
                              collocations=False, width=1000,
                              height=750, margin=2).generate_from_frequencies(filtered_word_freq)
        wordcloud.to_file(wordcloud_path)


def run_fetch(filename):
    fetch = Fetch(filename)
    fetch.run()


if __name__ == "__main__":
    items = list(Fetch.parse_search_items())
    filenames = [name[1] for name in items]

    args_lst = [filenames[i:i+4] for i in range(0, len(filenames), 4)]
    threads_lst = []
    for lst in args_lst:
        pool = ThreadPool()
        pool.map(run_fetch, lst)
        pool.close()
        pool.join()

    # for name in filenames:
    #     run_fetch(name)
    Fetch.run_all(filenames)