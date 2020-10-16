#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
from pymed.article import PubMedArticle


class Article(PubMedArticle):
    def get_pubtypes(self):
        path = ".//PublicationType"
        return [
            pubtype.text for pubtype in self.xml.findall(path) if pubtype is not None
        ]


def get_abs(file):
    text = ""
    tree = ET.parse(file)
    root = tree.getroot()
    for article in root.iter("PubmedArticle"):
        try:
            p = Article(xml_element=article)
            text += p.abstract
        except TypeError:
            continue
    return text


if __name__ == '__main__':
    text = get_abs(os.path.join("download", "2015_2016.xml"))
    print(text)
