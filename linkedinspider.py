from selenium import webdriver
import time
import json
import csv
import pandas as pd
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
from parsel import Selector
import logging
import os

LOG_LEVEL = logging.DEBUG


class LinkedinSpider:

    def __init__(self, username, password):
        """Initialization of this spider with user info
        """
        self.username = username
        self.password = password
        # self.browser = None
        self.options = webdriver.FirefoxOptions()
        self.options.headless = False
        self.options.set_preference

        # Turn off the Selenium geckodriver log
        # self.browser = webdriver.Firefox(
        #     options=self.options, service_log_path=os.devnull)

        self.browser = webdriver.Firefox(
            options=self.options, service_log_path="log/geckodriver.log")
        self.init_logging()

    def init_logging(self):
        """Initialize the logging env
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(LOG_LEVEL)
        # log to the console
        # handler = logging.StreamHandler()
        # log to a file
        handler = logging.FileHandler("log/spider.log", mode='a')
        handler.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(
            "\n[%(asctime)s] %(filename)s %(funcName)s at line %(lineno)s [%(levelname)s] \n\t %(message)s\n")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def restart(self, wait):
        """Close the browser and restart after a given time (seconds)

        Args:
            time (int): time waited between closed and reopen
        """
        self.browser.quit()
        time.sleep(wait)
        self.browser = webdriver.Firefox(
            options=self.options, service_log_path="log/geckodriver.log")

    def login(self):
        """Login in Linkedin with user info
        """
        browser = self.browser
        browser.get('https://www.linkedin.com/login')
        # locate email form by_id
        username = browser.find_element_by_id("username")
        username.send_keys(self.username)
        time.sleep(0.5)
        # locate password form by_id
        password = browser.find_element_by_id('password')
        password.send_keys(self.password)
        time.sleep(0.5)
        # locate submit button by_id
        login_button = browser.find_element_by_class_name(
            "login__form_action_container")
        login_button.click()
        time.sleep(0.5)

    def search(self, query: str) -> list:
        """Search Linked user by google search engine

        Args:
            query (str): query string

        Returns:
            list: linkedin user profile urls
        """
        self.logger.info(f"query string => {query}")
        browser = self.browser
        browser.get('https://www.google.com')
        time.sleep(2)
        search_box = browser.find_element_by_name('q')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)
        if "sorry/index?continue=" in browser.current_url:
            return -1
        # a_tags is a list of FirefoxWebElement
        a_tags = browser.find_elements_by_css_selector('div.r a')
        urls = [a_tag.get_attribute("href") for a_tag in a_tags]
        # filter those urls we need
        urls = [url for url in urls if "linkedin" in urlparse(url).netloc]
        self.logger.info(f"possible profiles urls: \n\t {urls}")
        return urls

    def parseInfo(self, url: str) -> dict:
        """Parse the basic info of a profile page for a given url

        Args:
            url (str): Linkedin profile url

        Returns:
            dict: Linkedin user profile information
        """
        self.browser.get(url)
        selector = Selector(self.browser.page_source)
        # extract name
        name = selector.xpath(
            '//*[starts-with(@class, "inline t-24 t-black t-normal break-words")]/text()').extract_first()
        name = name if name is None else name.strip()
        # extract info
        info = selector.xpath(
            '//*[starts-with(@class, "mt1 t-18 t-black t-normal break-words")]/text()').extract_first()
        info = info if info is None else info.strip()
        # extract profile url
        profile_url = self.browser.current_url
        # assembly these data to a dict
        information = {"name": name, "info": info, "profile_url": profile_url}
        self.logger.info(
            "Information extracted success!")
        self.logger.info(information)
        return information

    def close(self):
        if(self.browser is not None):
            self.browser.quit()
