#!/usr/bin/env python3
import os
from workflow import Fetch
from pubmed import Search_Pubmed

journal_list = []

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
        print(journal)
        journal_list.append(journal)

print(set(journal_list))
print(f"journals number: {len(set(journal_list))}")
