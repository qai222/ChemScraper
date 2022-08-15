import requests
from loguru import logger
from ratelimit import limits

from ChemScraper.settings import *
from ChemScraper.utils import find_between, download_file, FilePath, get_timestamp

"""
interact with NCBI entrez/eutils/sdq system 
"""


@limits(calls=4, period=1)
def request_entrez_query(
        eutils_method: str = "esearch", db: str = "pccompound",
        term: str = '"has src vendor"[Filter] AND ("Sigma-Aldrich"[SourceName] OR "Thermo Fisher Scientific"[SourceName])',
        retstart: int = 0, retmax: int = 10, retmode: str = "json", usehistory=True,
) -> dict:
    """
    construct url for an entrez/eutils query

    for eutils url, see
    - https://www.ncbi.nlm.nih.gov/books/NBK25500/
    - https://www.ncbi.nlm.nih.gov/books/NBK25499/

    for pubchem entrez, see
    - https://pubchemdocs.ncbi.nlm.nih.gov/advanced-search-entrez
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    url += f"{eutils_method}.fcgi?db={db}&term={term}&retstart={retstart}&retmax={retmax}&retmode={retmode}"
    if usehistory:
        url += "&usehistory=y"
    logger.info(f"request URL: {url}")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data


def _get_esearch_info(esearch_data: dict):
    querykey = esearch_data['esearchresult']['querykey']
    webenv = esearch_data['esearchresult']['webenv']
    count = esearch_data['esearchresult']['count']
    return querykey, webenv, count


@limits(calls=4, period=1)
def request_cachekey_for_esearch(querykey: int, webenv: str):
    url = 'https://pubchem.ncbi.nlm.nih.gov/list_gateway/list_gateway.cgi?action=entrez_to_cache'
    url += f'&entrez_db=pccompound&entrez_query_key={querykey}&entrez_webenv={webenv}'
    rep = requests.get(url)
    rep.raise_for_status()
    return find_between(rep.text, '<Response_cache-key>', '</Response_cache-key>')


def sdq_download_csv_with_cachekey(cachekey: str, count: int, saveas: FilePath, field_string="cid,mw,isosmiles"):
    """
    use sdq agent to download pubchem search result identified by a cachekey

    for sdq cases, see
    https://journals.flvc.org/cee/article/view/115508

    for sdq+lit-search cases, see
    https://vfscalfani.github.io/MATLAB-cheminformatics/live_scripts_html/PubChem_SDQ_LitSearch.html
    """
    url = 'https://pubchem.ncbi.nlm.nih.gov/sdq/sdqagent.cgi?'
    url += 'infmt=json&outfmt=csv'
    url += '&query={"download":"'
    url += field_string
    url += '","collection":"compound",'
    url += '"where":{"ands":[{"input":{"type":"netcachekey","idtype":"cid",'
    url += f'"key":"{cachekey}"'
    url += '}}]},"order":["relevancescore,desc"],"start":1,'
    url += f'"limit":{count},'
    url += '"downloadfilename":"PubChem_compound"}'
    logger.info(f"download from URL: {url}")
    download_file(url, saveas)


def download_vendor_compounds(
        vendors=VendorSources, saveas: FilePath = None, test_url=False,
        count_limit:int=None, field_string='cid,mw,isosmiles'
):
    """
    main function to download a list of pubchem compounds deposited by chemical vendors

    :param vendors: a tuple of chemical vendor names
    :param saveas: csv file to be saved as
    :param test_url: if True, no download will happen, only urls are printed in log
    :param count_limit: entry limit for downloading
    :param field_string: fields to be downloaded, default 'cid,mw,isosmiles'
    :return:
    """
    if saveas is None:
        saveas = f"PubchemVendorCompounds_{get_timestamp()}.csv"
    esearch_term = '"has src vendor"[Filter] AND '
    esearch_source = ['"{}"[SourceName]'.format(v) for v in vendors]
    esearch_source = " OR ".join(esearch_source)
    esearch_term += "(" + esearch_source + ")"
    logger.info(f"esearch for vendors: {vendors}")
    esearch_data = request_entrez_query(
        eutils_method="esearch", db="pccompound", term=esearch_term,
        retstart=0, retmax=10, retmode="json", usehistory=True,
    )
    logger.info("esearch success!")
    querykey, webenv, count = _get_esearch_info(esearch_data)
    logger.info(
        f"esearch saved at: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pccompound&query_key={querykey}&webenv={webenv}")
    logger.info(f"esearch count: {count}")
    cachekey = request_cachekey_for_esearch(querykey, webenv)
    logger.info(f"esearch converted to cache key at: https://pubchem.ncbi.nlm.nih.gov//#query={cachekey}")
    if not test_url:
        if count_limit is None:
            sdq_download_csv_with_cachekey(cachekey, count, saveas, field_string)
        else:
            sdq_download_csv_with_cachekey(cachekey, count_limit, saveas, field_string)
