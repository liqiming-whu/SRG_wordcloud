#!/usr/bin/env python3
import os
import sys
from entrezpy.esearch.esearcher import Esearcher
from entrezpy.efetch.efetcher import Efetcher
from entrezpy.efetch.efetch_analyzer import EfetchAnalyzer


user_email = "liqiming1914658215@gmail.com"


class PubmedAnalyzer(EfetchAnalyzer):
    """
    Derive a simple but specialized analyzer from the default EfetchAnalyzer.
    """

    def __init__(self, fname):
        """Init a GenomeAssenbler with NCBI summary data. In case we need to fetch
        multiple requests, e.g. WGS shotgun sequences, set a file handler as
        attribute."""
        super().__init__()
        self.fname = fname
        self.fh = None

    def analyze_result(self, response, request):
        """Set file handler and filename if it's the first query request. Otherwise
        append. """
        self.init_result(response, request)
        self.fh = open(self.fname, 'w', encoding='utf-8')
        result = replace_tags(response.getvalue())
        self.fh.write(result)
        self.fh.close()

    def isEmpty(self):
        """
        Since the analyzer is not using a entrezpy.base.result.EutilsResult to
        store results, we have to overwrite the method to report empty results.
        """
        if self.fh:
            return False
        return True


def replace_tags(text, reverse=False):
    tags = ['<sup>', '</sup>', '<sub>', '</sub>', '<i>', '</i>']
    re_tags = ['[^', '^]', '[_', '_]', '[/', '/]']
    for tag, re_tag in zip(tags, re_tags):
        if reverse:
            text = text.replace(re_tag, tag)
        else:
            text = text.replace(tag, re_tag)

    return text


def search_pubmed(journal, mindate, maxdate, email=user_email, retmax=500):
    e = Esearcher('Esearch', email)
    res = e.inquire({
        'db': 'pubmed',
        'term': journal,
        'sort': 'Date Released',
        'mindate': mindate,
        'maxdate': maxdate,
        'datetype': 'pdat',
        'retmax': retmax}).result
    return res.uids


def efetch_pubmed(idlist, outfile, email=user_email):
    e = Efetcher('Efetch', email)
    az = e.inquire({
        'db': 'pubmed',
        'id': idlist,
        'retmode': 'xml'}, PubmedAnalyzer(outfile)).get_result()
    return az


def search(journal, mindate, maxdate, outfile):
    idlist = search_pubmed(journal, mindate, maxdate)
    sys.stderr.write("\nFetching %d articles ......\n\n" % len(idlist))
    if len(idlist) > 0:
        efetch_pubmed(idlist, outfile)


if __name__ == '__main__':
    if not os.path.exists("stopwords_text"):
        os.mkdir("stopwords_text")
    date = ['1990\01\01', '2000\01\01', '2010\01\01', '2020\01\01']

    for mindate, maxdate in zip(date[:-1], date[1:]):
        search("Nature[ta] OR Science[ta] OR Cell[ta]", mindate, maxdate,
               "stopwords_text/"+mindate[:4]+"_"+maxdate[:4]+".xml")
