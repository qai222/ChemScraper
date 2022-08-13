import time

import pandas as pd
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ChemScraper.vscraper.se import WebElement, ec_visibility_of_all_elements, textify_elements


def get_thermo_fisher_patables_in_search(
        driver: webdriver.Chrome, cas: str, use_quickview=True, max_results=1,
):
    # TODO right now only the quick view of the first result is parsed

    search_url = fisher_search_url(cas)
    logger.info(f"getting searching url: {search_url}")
    driver.get(search_url)
    wait = WebDriverWait(driver, timeout=5)
    pa_buttons = wait.until(EC.visibility_of_all_elements_located(
        (By.XPATH, '//a[contains(@id, "qa_srch_res_quickView_")]')
    ))
    title_buttons = wait.until(EC.visibility_of_all_elements_located(
        (By.XPATH, '//a[contains(@id, "qa_srch_res_title_")]')
    ))
    if use_quickview:
        logger.info("using quick view from search results")
        if max_results != 1:
            raise NotImplementedError('only one result can be parsed for quickview mode')
        button = pa_buttons[0]
        logger.info("clicking quick view button...")
        ts1 = time.perf_counter()
        button.click()
        tr_elements = wait.until(
            EC.visibility_of_all_elements_located(
                (By.XPATH, '//table[contains(@class, "qv_table")]//tr[contains(@class, "qvTRow")]')
            )
        )
        th_elements = wait.until(
            EC.visibility_of_all_elements_located(
                (By.XPATH, '//table[contains(@class, "qv_table")]//tr[@class="header-row"]//th')
            )
        )
        cols = textify_elements(th_elements)
        cols[0] = 'sds_url'
        cols = ['product_url', ] + cols
        rows = []
        for tr in tr_elements:
            tds = tr.find_elements(By.TAG_NAME, 'td')
            tds = wait.until(ec_visibility_of_all_elements(tds))
            row_values = []
            for icell, cell in enumerate(tds):
                cell: WebElement
                if icell == 0:
                    product_link = None
                    sds_link = None
                    links = cell.find_elements(By.TAG_NAME, 'a')
                    links = wait.until(ec_visibility_of_all_elements(links))
                    try:
                        product_link, sds_link = links
                        product_link = product_link.get_attribute('href')
                        sds_link = sds_link.get_attribute('href')
                    except Exception as e:
                        logger.critical('error in parsing links (first cell)')
                        # logger.error(e)
                    row_values += [product_link, sds_link]
                else:
                    row_values.append(cell.text)
            rows.append(row_values)
        logger.info('parsed quick view table in: {:.3f} s'.format(time.perf_counter() - ts1))
        df = pd.DataFrame(rows, columns=cols)
        return df
    else:
        logger.info("using title links from search results")
        dfs = []
        for title_button in title_buttons[:max_results]:
            product_url = title_button.get_attribute('href')
            try:
                df = get_thermo_fisher_patable(driver, product_url)
                dfs.append(df)
            except Exception as e:
                logger.critical(f'FAILED to extract patable: {product_url}')
                # logger.error(e)
                continue
        return pd.concat(dfs, axis=0, ignore_index=True)


def get_thermo_fisher_patable(driver: webdriver.Chrome, product_url: str, sleep_for_price_label=0.5) -> pd.DataFrame:
    """
    scraping the product page
    """
    logger.info(f"thermo-fisher product url: {product_url}")
    driver.get(product_url)
    wait = WebDriverWait(driver, timeout=5)
    ts1 = time.perf_counter()
    quantity_buttons = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//div[contains(@id, "attributeButton_Quantity")]')))
    data = []
    for button in quantity_buttons:
        button.click()
        time.sleep(sleep_for_price_label)  # wait for price_label to change
        quantity = button.text
        logger.info(f'clicked button: {quantity}')
        try:
            price_label = wait.until(EC.visibility_of_element_located((By.XPATH, '//label[@class="price"]')))
            logger.info(f'price label is: {price_label.text}')
            price_label = price_label.text
            price, unit = price_label.strip().split("/")
        except Exception as e:
            logger.critical(f'failed to extract price_label: {quantity}')
            # logger.error(e)
            price = None
            unit = None
        try:
            sds_link = wait.until(EC.visibility_of_element_located(
                (By.XPATH, '//a[@id="qa_msds_item_link"]')
            )).get_attribute('href')
        except Exception as e:
            logger.critical(f'failed to extract sds url: {quantity}')
            # logger.error(e)
            sds_link = None
        data.append({
            'product_url': product_url,
            'sds_url': sds_link,
            'quantity': quantity,
            'price': price,
            'unit': unit,
        })
    logger.info("scraped product url in: {:.3f} s".format(time.perf_counter() - ts1))
    df = pd.DataFrame.from_records(data)
    return df


def fisher_search_url(cas: str):
    url = f"https://www.fishersci.com/us/en/catalog/search/products?keyword={cas}"
    return url


if __name__ == '__main__':
    from ChemScraper.vscraper.se import get_chrome_driver

    # driver = get_chrome_driver(headless=False)
    driver = get_chrome_driver(headless=True)
    CAS = "107-15-3"
    # df = get_thermo_fisher_patables_in_search(driver, CAS, True)
    # print(df)
    df = get_thermo_fisher_patables_in_search(driver, CAS, False)
    print(df)
    # url = "https://www.fishersci.com/shop/products/acetylsalicylic-acid-99-thermo-scientific/AC158185000#?keyword=50-78-2"
    # url = remove_url_query(url)
    # get_thermo_fisher_patable(driver, url)
