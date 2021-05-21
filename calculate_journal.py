#!/usr/bin/env python3
import os
from workflow import Fetch
from pubmed import Search_Pubmed

journal_list = []

logfile = open("jour_count.log", "w")

for _, dirname in Fetch.parse_search_items():
    if not os.path.exists(os.path.join("results", dirname)):
        continue
    if not os.path.exists(os.path.join("results", dirname, "articles")):
        print(f"No {dirname}")
        continue
    art_dir = os.path.join("results", dirname, "articles")

    for art in os.listdir(art_dir):
        pmid = art.replace(".txt", "")
        journal = Search_Pubmed.get_journal(pmid)
        print(f"{pmid} {journal}")
        logfile.write(f"{pmid} {journal}\n")
        journal_list.append(journal)

print(set(journal_list))
logfile.write(f"{set(journal_list)}\n")
print(f"journals number: {len(set(journal_list))}")
logfile.write(f"journals number: {len(set(journal_list))}")
logfile.close()