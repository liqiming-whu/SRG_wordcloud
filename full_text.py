#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException, WebDriverException


class Article:
    browser = webdriver.Chrome()
    base_url = 'https://doi.org/'
    wait = WebDriverWait(browser, 60)
    browser.set_page_load_timeout(30)
    browser.set_script_timeout(10)

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
        except InvalidSessionIdException:
            self.logfile.log("Article {} doi: {} invalid session id.\n".format(self.id, self.doi))
            return "Error"
        except WebDriverException:
            self.logfile.log("Article {} doi: {} conection closed.\n".format(self.id, self.doi))
            return "Error"
        finally:
            return ""

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
            try:
                text_list = [p.text for p in elements]
            except Exception:
                text_list = []
            while not text_list and flag < 3:
                self.logfile.log("Request timeout, retrying...\n")
                self.request()
                elements = self.browser.find_elements_by_tag_name('p')
                flag += 1
                try:
                    text_list = [p.text for p in elements]
                except Exception:
                    text_list = []

            if not text_list:
                self.logfile.log("Request failed. Article {} doi: {}.\n".format(self.id, self.doi))
                return ""
            text = "".join(text_list)
            if len(text) < 500:
                return ""
                self.logfile.log("Article {} doi: {} Full text not found.\n".format(self.id, self.doi))
            self.logfile.log("Article {} doi: {} saved.\n".format(self.id, self.doi))
        return text
