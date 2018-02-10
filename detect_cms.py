# -*- coding: utf8 -*-

import logging
import requests
import six
from wad.detection import Detector
from bs4 import BeautifulSoup


TIMEOUT = 3


class CmsDetector(Detector):
    def __init__(self):
        super().__init__()

    def detect(self, url, limit=None, exclude=None, timeout=TIMEOUT):
        logging.info("- %s", url)
        original_url = url
        if not self.expected_url(url, limit, exclude):
            return {}
        page = self.get_page(url=url, timeout=timeout)
        if not page:
            return {}
        url = self.get_new_url(page)
        if url != original_url:
            logging.info("` %s", url)
            if not self.expected_url(url, limit, exclude):
                return {}
        url = self.normalize_url(url)
        # get in bytes content
        content = self.get_content(page, url)
        if content is None:
            return {}
        # else convert into str
        content = self.convert_content_str(content)
        tools = self.get_site_url_tools(content, page, url)
        return tools

    def get_site_url_tools(self, content, page, url):
        """
        Get the data from site:
        :param content:
        :param page:
        :param url:
        :return: tuple: url and findings info site
        """

        keywords = self.extract_keywords_from_meta_title(content)
        text = BeautifulSoup(content, 'html.parser').find_all("title")

        findings = []
        findings += self.check_url(url)
        if page:
            findings += self.check_headers(page.info())  # 'headers'
        if content:
            findings += self.check_meta(content)  # 'meta'
            findings += self.check_script(content)  # 'script'
            findings += self.check_html(content)  # 'html'
        findings += self.additional_checks(page, url, content)
        self.follow_implies(findings)  # 'implies'
        self.remove_duplicates(findings)
        self.remove_exclusions(findings)  # 'excludes'
        self.add_categories(findings)
        cms = self.type_cms(findings)
        return url, findings, keywords, cms

    @staticmethod
    def type_cms(findings):
        """
        Show only type cms if it found.
        :param findings: list of dicts tools of site
        :return: cms
        """
        list_type = ["cms", "cms,blogs"]
        try:
            type_cms = next(item for item in findings if item["type"] in list_type)
            return type_cms["app"]
        except:
            print("No cms")

    def find_items_for_client_test(self, url, keyword):
        """
        Find items for client test on portal.
        :param url:
        :param keyword:
        :return:item_for_data
        """
        feed_link = self.build_link(url, keyword)
        item_for_data = self.parse_page(feed_link)
        return item_for_data

    def extract_keywords_from_meta_title(self, content):
        """
        Extract keywords from meta tags. If no any meta, try to get keywords from title of page
        :param content:
        :return: key_data: return keywords list
        """
        for_search_tag = BeautifulSoup(content, 'html.parser')
        metas = for_search_tag.find_all('meta')
        key_data = [meta.attrs['content'] for meta in metas if
                    'name' in meta.attrs and meta.attrs['name'] == 'description']
        if key_data:
            key_data = key_data[0].replace(',', '').split(' ')
        else:
            title = for_search_tag.find('title').text
            if title:
                key_data = title.split(' ')
        # get only words with number of letters > 3
        keywords = self.get_keywords_for_test(key_data)
        return keywords

    @staticmethod
    def get_keywords_for_test(key_data, number_keywords=3):
        """
        Check key_data if we have words with number of letters > 3, extract its.
        :param key_data: list of keywords
        :param number_keywords: count of keywords
        :return: keywords: list of words with number of letters > 3
        """
        keywords = []
        for word in key_data:
            if len(word) > 3:
                keywords.append(word)
        return keywords[:number_keywords]

    @staticmethod
    def convert_content_str(content):
        """
        Convert the content site from bytes to str format.
        :param content: content from site in bytes
        :return: content: in str format
        """
        if six.PY3:
            # if python3 convert in str
            content = content.decode()
        return content


    @staticmethod
    def build_link(url, keyword):
        """
        Get the url from WP site with keywords for feeds data.
        :param url:
        :param keyword: keyword for test link
        :return: url_for_parse: string
        """
        if url.endswith('/'):
            url = url[:-1]
        url_for_parse = url + '/?s=' + keyword + '&feed=rss2'
        return url_for_parse

    @staticmethod
    def parse_page(url, count_of_items=3):
        """
        Info for client's search test in portal.
        From keyword plus url get the data of title, description, link.
        If there are many items, get only 3.
        :param url:
        :param count_of_items: by default get 3 items
        :return: result: list of three items constructed from title, description, link
        """
        feed_item = BeautifulSoup(requests.get(url).text, 'xml').find_all('item')[:count_of_items]
        result = []
        for row in feed_item:
            title = row.find("title")
            title.append(title.text)
            description = row.find("description")
            description.append(description.text)
            link = row.find("link")
            link.append(link.text)
            item = dict(title=title.text, description=description.text, link=link.text)
            result.append(item)
        return result
