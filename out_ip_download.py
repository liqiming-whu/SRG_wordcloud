#!/usr/bin/env python3
import os
from workflow import Fetch, LogFile
from pubmed import Search_Pubmed
from full_text import Article

logfile = LogFile("out_ip_download.log")

count = 0

out_path = os.path.join("results", "out_download_articles")

if not os.path.exists(out_path):
    os.mkdir(out_path)

for _, dirname in Fetch.parse_search_items():
    if not os.path.exists(os.path.join("results", dirname)):
        continue
    if not os.path.exists(os.path.join("results", dirname, "articles")):
        continue
    art_dir = os.path.join("results", dirname, "articles")

    for art in os.listdir(art_dir):
        pmid = art.replace(".txt", "")
        if os.path.exists(os.path.join(out_path, pmid+".txt")):
            count += 1
            continue
        source = Search_Pubmed.get_source(pmid)
        try:
            _, doi = Fetch.parse_source(source)
        except Exception:
            print(f"Article {pmid} doi not found.")
            continue
        try:
            page = Article(pmid, doi, logfile)
        except Exception:
            print(f"Article {pmid} connect failed.")
            continue
        page_text = page.get_text()
        if not os.path.exists(os.path.join(out_path, pmid+".txt")):
            with open(os.path.join(out_path, pmid+".txt"), "w") as o:
                o.write(page_text)
                count += 1


print(f"Total {count} articles")