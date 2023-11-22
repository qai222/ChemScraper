import pprint

from ChemScraper import get_chrome_driver
from ChemScraper.vscraper.sigma_aldrich import *

browser_driver = get_chrome_driver()

prop = get_sigma_aldrich_properties(browser_driver, "https://www.sigmaaldrich.com/US/en/product/sial/e26266")
pprint.pp(prop)
