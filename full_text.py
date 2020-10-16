#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class Article:
    browser = webdriver.Chrome()
    base_url = 'https://doi.org/'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}
    wait = WebDriverWait(browser, 60)
    browser.set_page_load_timeout(30)
    browser.set_script_timeout(5)

    def __init__(self, pmid, doi, log):
        self.doi = doi
        self.url = self.base_url + doi
        self.logfile = log
        self.id = pmid

    def request(self):
        try:
            self.browser.get(self.url)
        except TimeoutException:
            self.browser.execute_script('window.stop()')
        title = self.browser.title

        return title

    def get_text(self):
        title = self.request()
        if title.startswith("Error"):
            self.logfile.log("Article {} doi: {} not found.\n".format(self.id, self.doi))
            return ""
        else:
            elements = self.browser.find_elements_by_tag_name('p')
            flag = 0
            while not elements and flag < 3:
                self.logfile.log("Request timeout, retrying...\n")
                self.request()
                elements = self.browser.find_elements_by_tag_name('p')
                flag += 1
            if not elements:
                self.logfile.log("Request failed. Article {} doi: {}.\n".format(self.id, self.doi))
                return ""
            text_list = [p.text for p in elements]
            text = "".join(text_list)
            self.logfile.log("Article {} doi: {} saved.\n".format(self.id, self.doi))
        return text
