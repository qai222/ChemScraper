import pprint

import requests
from ratelimit import limits
from requests.exceptions import HTTPError

from ChemScraper.settings import *
from ChemScraper.utils import traverse_json

"""
interact with pug view
https://pubchemdocs.ncbi.nlm.nih.gov/pug-view

useful gist for cas rn extraction
https://gist.github.com/KhepryQuixote/00946f2f7dd5f89324d8
"""


@limits(calls=4, period=1)
def request_pug_view(cid: int, task='cas') -> dict:
    if task == 'cas':
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{}/JSON?heading=CAS".format(cid)
    elif task == 'category':
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/categories/compound/{}/JSON".format(cid)
    else:
        raise NotImplementedError(f"unknown task: {task}")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def _get_cas_number_from_pug_view(data: dict):
    for v in traverse_json(data):
        leaf = v[-1]
        if not isinstance(leaf, str):
            continue
        if "https://commonchemistry.cas.org/detail" in leaf:
            return leaf.replace("https://commonchemistry.cas.org/detail?cas_rn=", "")
    return None


def _get_vendor_link_from_pug_view(data: dict) -> dict[str, str]:
    try:
        cats = data['SourceCategories']['Categories']
        vendor_cats = [cat for cat in cats if 'Chemical Vendors' == cat['Category']]
        assert len(vendor_cats) == 1
        vendor_cat = vendor_cats[0]
        vendor_sources = [source for source in vendor_cat['Sources'] if source['SourceName'] in VendorSources]
        return {vs['SourceName']: vs['SourceRecordURL'] for vs in vendor_sources}
    except (KeyError, AssertionError) as e:
        return dict()


def get_vendor_links(cid: int):
    try:
        data = request_pug_view(cid, 'category')
        return _get_vendor_link_from_pug_view(data)
    except HTTPError:
        return dict()


def get_cas_number(cid: int):
    try:
        data = request_pug_view(cid, 'cas')
        return _get_cas_number_from_pug_view(data)
    except HTTPError:
        return None
