#!/usr/bin/env python3
import os
import csv
import time
from pubmed import Search_Pubmed
from full_text import Article
from generate_stopwords import clean_str
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from wordcloud import WordCloud
import matplotlib.pyplot as plt


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
    def __init__(self, logfile):
        self.logfile = logfile

    def __str__(self):
        return "Fetch {}".format(self.query)

    __repr__ = __str__

    @property
    def stopwords(self):
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

    def search(self, query, filename):
        if not os.path.exists("results"):
            os.mkdir("results")
        outdir = os.path.join("results", filename)
        if not os.path.exists(outdir):
            os.mkdir(outdir)
            search_results = Search_Pubmed(query)
            self.logfile.log("Query: {}, Count: {}.".format(query, search_results.count))
            csvfile = os.path.join(outdir, filename+"_info.csv")
            search_results.save_info(csvfile)

        return filename

    def start_search(self, species=None):
        if species:
            items = list(self.parse_search_items())
            species_id = int(species) - 1
            query, filename = items[species_id]
            return self.search(query, filename)
        else:
            name_list = []
            for query, filename in items:
                name = self.search(query, filename)
                name_list.append(name)
            return name_list

    def path(self, filename, type=None):
        if type == "info":
            return os.path.join("results", filename, "{}_info.csv".format(filename))
        if type == "fulltext":
            return os.path.join("results", filename, "{}_full.txt".format(filename))
        return os.path.join("results", filename)

    def parse_source(self, source):
        fileds = source.split("doi:")
        journal = fileds[0].strip()
        doi = fileds[1].strip().rstrip(".")

        return journal, doi

    def get_full_text(self, filename):
        info = open(self.path(filename, type="info"))
        reader = csv.reader(info)
        count = 0
        with open(os.path.join(self.path(filename), "{}_full.txt".format(filename)), "w", encoding="utf-8") as f:
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
        self.logfile.log("{} articles have been saved.\n".format(count))
        Article.browser.close()

    def run(self):
        filename = self.start_search(5)
        self.get_full_text(filename)


if __name__ == "__main__":
    log = LogFile("results.log")
    fetch = Fetch(log)
    fetch.run()
    log.close()
