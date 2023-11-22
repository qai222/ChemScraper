import time

import pandas as pd
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ChemScraper.utils import chunks
from ChemScraper.vscraper.se import textify_elements


def get_sigma_aldrich_patable(driver: webdriver.Chrome, product_url: str) -> pd.DataFrame:
    """
    scraping the product page

    :param driver: Se driver
    :param product_url: either from pubchem or from a sigma-aldrich search
    :return:
    """
    logger.info(f"sigma-aldrich product url: {product_url}")
    driver.get(product_url)
    wait = WebDriverWait(driver, timeout=5)
    ts1 = time.perf_counter()
    # stricter path to elements in the first table
    cols = wait.until(EC.presence_of_all_elements_located((By.XPATH, '/descendant::table[1]/thead/tr/th')))
    rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, '/descendant::table[1]/tbody/tr/td')))
    logger.info("page ready after: {:.3f} s".format(time.perf_counter() - ts1))
    ncols = len(cols)
    assert len(rows) % ncols == 0
    rows = chunks(rows, ncols)
    rows = [textify_elements(r) for r in rows]
    cols = textify_elements(cols)
    df = pd.DataFrame(rows)
    df.columns = cols
    df['url'] = [product_url, ] * len(rows)
    return df


def get_sigma_aldrich_properties(driver, product_url: str) -> dict[str, str]:
    logger.info(f"sigma-aldrich product url: {product_url}")
    driver.get(product_url)
    wait = WebDriverWait(driver, timeout=5)
    ts1 = time.perf_counter()
    try:
        property_toggle = wait.until(EC.element_to_be_clickable((By.ID, 'properties-expansion-toggle')))
        # .click does not work, use this from https://stackoverflow.com/a/77055003/18029270
        property_toggle.send_keys(Keys.RETURN)
    except Exception:
        pass

    property_divs = wait.until(EC.presence_of_all_elements_located((By.ID, 'pdp-properties--table')))

    logger.info("page ready after: {:.3f} s".format(time.perf_counter() - ts1))
    properties = dict()
    for prop_div in property_divs:
        items = prop_div.text.split("\n")
        assert len(items) >= 2, f"expected more than 2 items from the text: {prop_div.text}"
        name, value = items[0], "\n".join(items[1:])
        properties[name.strip()] = value.strip()
    return properties


def get_sigma_aldrich_properties_from_cas(driver, cas: str) -> dict[str, str]:
    url = sigma_search_url(cas)
    logger.info(f"sigma-aldrich search url: {url}")
    driver.get(url)
    product_elements_locator = (By.XPATH, '//a[contains(@href, "/product/")]')
    wait = WebDriverWait(driver, timeout=15)
    ts1 = time.perf_counter()
    product_elements = wait.until(EC.presence_of_all_elements_located(product_elements_locator))
    logger.info("page ready after: {:.3f} s".format(time.perf_counter() - ts1))
    links = [elem.get_attribute('href') for elem in product_elements]
    for link in links:
        try:
            prop_dict = get_sigma_aldrich_properties(driver, link)
            return prop_dict
        except Exception as e:
            logger.critical(f'FAILED to extract properties: {link}')
            logger.error(e)
            continue
    logger.critical(f'FAILED to find properties for: {cas}')
    return {}


def get_sigma_aldrich_properties_from_mf(driver, mf: str) -> dict[str, str]:
    url = sigma_search_url_mf(mf)
    logger.info(f"sigma-aldrich search url: {url}")
    driver.get(url)
    product_elements_locator = (By.XPATH, '//a[contains(@href, "/product/")]')
    wait = WebDriverWait(driver, timeout=15)
    ts1 = time.perf_counter()
    try:
        product_elements = wait.until(EC.presence_of_all_elements_located(product_elements_locator))
    except TimeoutException:
        logger.critical(f'FAILED to find properties for: {mf}')
        return {}
    logger.info("page ready after: {:.3f} s".format(time.perf_counter() - ts1))
    links = [elem.get_attribute('href') for elem in product_elements]
    for link in links:
        try:
            prop_dict = get_sigma_aldrich_properties(driver, link)
            return prop_dict
        except Exception as e:
            logger.critical(f'FAILED to extract properties: {link}')
            logger.error(e)
            continue
    logger.critical(f'FAILED to find properties for: {mf}')
    return {}


def get_sigma_aldrich_patables(driver, cas: str) -> pd.DataFrame:
    url = sigma_search_url(cas)
    logger.info(f"sigma-aldrich search url: {url}")
    driver.get(url)
    product_elements_locator = (By.XPATH, '//a[contains(@href, "/product/")]')
    wait = WebDriverWait(driver, timeout=5)
    ts1 = time.perf_counter()
    product_elements = wait.until(EC.visibility_of_all_elements_located(product_elements_locator))
    logger.info("page ready after: {:.3f} s".format(time.perf_counter() - ts1))
    links = [elem.get_attribute('href') for elem in product_elements]
    unique_links = []
    dataframes = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)
            try:
                df = get_sigma_aldrich_patable(driver, link)
                dataframes.append(df)
            except Exception as e:
                logger.critical(f'FAILED to extract patable: {link}')
                # logger.error(e)
                continue

    logger.info(f"sigma-aldrich search returns # of products: {len(dataframes)}")
    return pd.concat(dataframes, axis=0, ignore_index=True)


def sigma_sds_url_from_product_url(product_url: str):
    product = product_url.replace("https://www.sigmaaldrich.com/catalog/product", "")
    sds_url = f"https://www.sigmaaldrich.com/US/en/sds/{product}"
    return sds_url


def sigma_search_url(cas: str):
    # TODO the perpage param does not work in browser, it's always 30, need to automate page turn
    url = f"https://www.sigmaaldrich.com/US/en/search/{cas}?focus=products&page=1&perpage=30&sort=relevance&term={cas}&type=cas_number"
    return url


def sigma_search_url_mf(mf: str):
    url = f"https://www.sigmaaldrich.com/US/en/search/{mf}?focus=products&page=1&perpage=30&sort=relevance&term={mf}&type=mol_form"
    return url
