#!/usr/bin/env python3
import os
import csv
import time
from functools import wraps
from pubmed import Search_Pubmed
from generate_stopwords import clean_str
from nltk.tokenize import word_tokenize
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
        stopwords = set(line.rstrip() for line in open("stopwords.txt"))
        add = set(line.rstrip() for line in open("supplementary_stopwords.txt"))
        stopwords = stopwords | add

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
                elif not os.path.getsize(path):
                    return func(self)
                else:
                    return None
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
        self.logfile.log("Query: {}, Count: {}.".format(query, count))
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
            return os.path.join("results", self.filename, "{}_words_freq.txt".format(self.filename))
        if type == "pdf":
            return os.path.join("results", self.filename, "{}.pdf".format(self.filename))

        return os.path.join("results", self.filename)

    @staticmethod
    def fetch_path(filename, type=None):
        if type == "info":
            return os.path.join("results", filename, "{}_info.csv".format(filename))
        if type == "fulltext":
            return os.path.join("results", filename, "{}_full.txt".format(filename))
        if type == "freq":
            return os.path.join("results", filename, "{}_words_freq.txt".format(filename))
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
        count = 0
        full_text_path = os.path.join(self.path(), "{}_full.txt".format(self.filename))
        from full_text import Article
        with open(full_text_path, "w", encoding="utf-8") as f:
            text = ""
            next(reader)
            for row in reader:
                pmid = row[0]
                source = row[3]
                _, doi = self.parse_source(source)
                page = Article(pmid, doi, self.logfile)
                page_text = page.get_text()
                if page_text:
                    count += 1
                    text += page_text
            f.write(text)
        Article.browser.close()
        self.logfile.log("{} articles have been saved.\n".format(count))

    @exec(type="freq")
    def save_word_freq(self):
        text_path = self.path(type='fulltext')
        text = open(text_path).read()
        words = word_tokenize(clean_str(text))
        fdist = FreqDist(words)
        words = set([word[0] for word in fdist.most_common(200)])
        words = list(words - self.stopwords)
        word_freq_path = os.path.join(self.path(), "{}_words_freq.txt".format(self.filename))
        with open(word_freq_path, "w", encoding="utf-8") as f:
            f.write("\n".join(words))

    @exec(type="pdf")
    def wordcloud(self):
        text_path = self.path(type='fulltext')
        text = open(text_path).read()
        wordcloud_path = os.path.join(self.path(), "{}.pdf".format(self.filename))
        wordcloud = WordCloud(background_color="white",
                              stopwords=self.stopwords, scale=3,
                              collocations=False, width=1000,
                              height=750, margin=2).generate(text)
        wordcloud.to_file(wordcloud_path)

    def run(self):
        self.logfile.log("Start fetch {}...".format(self.filename))
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
            text += open(text_path).read()
        wordcloud_path = os.path.join("results", "all.pdf")
        wordcloud = WordCloud(background_color="white",
                              stopwords=Fetch.stopwords(), scale=2,
                              collocations=False, width=1000,
                              height=750, margin=2).generate(text)
        wordcloud.to_file(wordcloud_path)


def run_fetch(filename):
    fetch = Fetch(filename)
    fetch.run()


if __name__ == "__main__":
    items = list(Fetch.parse_search_items())
    filenames = [name[1] for name in items[:4]]

    args_lst = [filenames[i:i+4] for i in range(0, len(filenames), 4)]
    threads_lst = []
    for lst in args_lst:
        pool = ThreadPool()
        pool.map(run_fetch, lst)
        pool.close()
        pool.join()

    Fetch.run_all(filenames)
