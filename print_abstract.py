#!/usr/bin/env python3
import os
from Bio import Entrez, Medline
from wordcloud import WordCloud
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from generate_stopwords import clean_str


Entrez.email = "liqiming1914658215@gmail.com"
Entrez.api_key = "c80ce212c7179f0bbfbd88495a91dd356708"

stopwords_path = os.path.jon('data', 'stopwords.txt')
sup_stopwords_path = os.path.join('data', 'supplementary_stopwords.txt')
stopwords = set(line.rstrip() for line in open(stopwords_path))
add = set(line.rstrip() for line in open(sup_stopwords_path))
stopwords = stopwords | add


def get_count(database, term):
    handle = Entrez.egquery(term=term)
    record = Entrez.read(handle)
    for row in record["eGQueryResult"]:
        if row["DbName"] == database:
            count = row["Count"]
    return count


def search(database, keywords, count):
    handle = Entrez.esearch(db=database, term=keywords, retmax=count)
    record = Entrez.read(handle)
    return record["Count"], record["IdList"]


def get_abstract(database, idlist):
    text = ""
    handle = Entrez.efetch(db=database, id=idlist, rettype="medline", retmode="text")
    records = Medline.parse(handle)
    for record in records:
        try:
            pmid = str(record.get("PMID", "?"))
            print("pmid:", pmid)
            abstract = record.get("AB", "?")
            abstract = " ".join(list(set(abstract.split())))
            text += abstract
        except Exception:
            continue
    return text


def save_text(text):
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(text)


def save_word_list(text):
    words = word_tokenize(clean_str(text))
    fdist = FreqDist(words)
    words = fdist.most_common(200)
    with open("words_freq.txt", "w", encoding="utf-8") as f:
        for word in words:
            if word[0] not in stopwords:
                print(word[0], file=f)


def wordcloud(text):
    """
    params:
    stopwords:set, default:None
    collections:Include binary phrases or not
    """
    wordcloud = WordCloud(background_color="white", stopwords=stopwords, scale=4,
                          collocations=False, width=1000, height=750, margin=2).generate(text)
    wordcloud.to_file("Zebrafish_abstract.pdf")


def main():
    query = "Danio rerio OR Zebrafish AND sex reversal"
    if(os.path.exists("abstract_result.txt")):
        text = open("abstract_result.txt").read()
        print("results laoded.")
    else:
        count = get_count("pubmed", query)
        print("count:", count)
        _, idlist = search("pubmed", query, count)
        text = get_abstract("pubmed", idlist)
        save_text(text)
    save_word_list(text)
    wordcloud(text)


if __name__ == '__main__':
    main()
