from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from ChemScraper.utils import get_folder

"""
selenium driver set up
"""

ua = UserAgent()  # error msg for the first run


def textify_elements(eles: list[WebElement]):
    return [e.text for e in eles]


def get_chrome_driver(headless=True) -> webdriver.Chrome:
    window_size = "1920,1080"
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=%s" % window_size)
    options.add_argument(f'user-agent={ua.chrome}')
    options.add_experimental_option("prefs", {
        "download.default_directory": f"{get_folder(__file__)}",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    if headless:
        options.add_argument("--headless")  # https://stackoverflow.com/questions/16180428/
    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver


def ec_visibility_of_all_elements(elements):
    def _predicate(driver):
        try:
            for element in elements:
                if EC._element_if_visible(element, visibility=False):
                    return False
            return elements
        except EC.StaleElementReferenceException:
            return False

    return _predicate


def ec_clickable_of_all_elements(elements):
    def _predicate(driver):
        for element in elements:
            if not EC.element_to_be_clickable(element):
                return False
        return elements

    return _predicate
