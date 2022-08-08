import time
from collections import defaultdict
from typing import Union

import requests
from loguru import logger
from ratelimit import limits
from requests.exceptions import HTTPError

from ChemScraper.schema import Compound
from ChemScraper.utils import find_between, download_file, FilePath, get_timestamp, removefile, inchi2smiles

"""
interact with power-user-gateway directly using xml
https://pubchemdocs.ncbi.nlm.nih.gov/power-user-gateway
"""


def _generate_idxc_pct_xml(identifiers: list[str], input_type, output_type: str = "cid"):
    header = '<?xml version="1.0"?>\n<!DOCTYPE PCT-Data PUBLIC "-//NCBI//NCBI PCTools/EN" "NCBI_PCTools.dtd">\n'
    body_top = """<PCT-Data>\n<PCT-Data_input>\n<PCT-InputData>\n<PCT-InputData_query>\n<PCT-Query>\n<PCT-Query_type>\n<PCT-QueryType>\n<PCT-QueryType_id-exchange>\n<PCT-QueryIDExchange>\n<PCT-QueryIDExchange_input>\n<PCT-QueryUids>"""
    body_bot = f"""</PCT-QueryUids>\n</PCT-QueryIDExchange_input>\n<PCT-QueryIDExchange_operation-type value="same"/>\n<PCT-QueryIDExchange_output-type value="{output_type}"/>\n<PCT-QueryIDExchange_output-method value="file-pair"/>\n<PCT-QueryIDExchange_compression value="none"/>\n</PCT-QueryIDExchange>\n</PCT-QueryType_id-exchange>\n</PCT-QueryType>\n</PCT-Query_type>\n</PCT-Query>\n</PCT-InputData_query>\n</PCT-InputData>\n</PCT-Data_input>\n</PCT-Data>"""
    if input_type == 'smiles':
        body = "<PCT-QueryUids_smiles>\n"
        for smi in identifiers:
            body += f"<PCT-QueryUids_smiles_E>{smi}</PCT-QueryUids_smiles_E>\n"
        body += "</PCT-QueryUids_smiles>\n"
    elif input_type == 'cid':
        body = """<PCT-QueryUids_ids>\n<PCT-ID-List>\n<PCT-ID-List_db>pccompound</PCT-ID-List_db>\n<PCT-ID-List_uids>"""
        for cid in identifiers:
            body += f"<PCT-ID-List_uids_E>{cid}</PCT-ID-List_uids_E>"
        body += """</PCT-ID-List_uids>\n</PCT-ID-List>\n</PCT-QueryUids_ids>"""
    elif input_type == 'inchi':
        body = "<PCT-QueryUids_inchis>\n"
        for inchi in identifiers:
            body += f"<PCT-QueryUids_inchis_E>{inchi}</PCT-QueryUids_inchis_E>\n"
        body += "</PCT-QueryUids_inchis>\n"
    else:
        raise ValueError(f"Unknown identifier type: {input_type}")
    return header + body_top + body + body_bot


def _generate_pug_fetch_xml(reqid: str):
    request_xml = f"""<PCT-Data>
<PCT-Data_input>
<PCT-InputData>
<PCT-InputData_request>
<PCT-Request>
<PCT-Request_reqid>{reqid}</PCT-Request_reqid>
<PCT-Request_type value="status"/>
</PCT-Request>
</PCT-InputData_request>
</PCT-InputData>
</PCT-Data_input>
</PCT-Data>"""
    return request_xml


@limits(calls=4, period=1)
def request_pug(xml):
    resp = requests.post(
        url="https://pubchem.ncbi.nlm.nih.gov/pug/pug.cgi",
        data=xml,
    )
    return resp


def request_convert_identifiers(
        identifiers: Union[list[str], list[int]], input_type: str = 'smiles', output_type: str = 'cids',
        tmpfile: FilePath = None,
        total_time_limit=500, retry_interval=10,
):
    """
    :param input_type: 'smiles', 'cid', 'inchi'
    :param output_type: 'smiles', 'cid', 'inchi', 'iupac'

    idx webpage
    https://pubchem.ncbi.nlm.nih.gov/idexchange/idexchange.cgi

    pug doc:
    https://pubchemdocs.ncbi.nlm.nih.gov/power-user-gateway

    old examples pubchem pug:
    https://depth-first.com/articles/2007/06/11/hacking-pubchem-learning-to-speak-pug/
    """
    if tmpfile is None:
        tmpfile = f"converted_I{input_type}O{output_type}_{get_timestamp()}.txt"
    # compose and submit idxc xml
    xml = _generate_idxc_pct_xml(identifiers, input_type, output_type)
    resp = request_pug(xml)
    resp.raise_for_status()

    try:
        reqid = find_between(resp.text, '<PCT-Waiting_reqid>', '</PCT-Waiting_reqid>')
    except IndexError as e:
        logger.error(resp.text)
        raise e

    fetch_xml = _generate_pug_fetch_xml(reqid)

    # fetch the request id, retry if not finished
    time.sleep(1)
    time_counter = 0.0
    while time_counter < total_time_limit:
        logger.info(f"fetching request: {reqid}")
        try:
            fetch_resp = request_pug(fetch_xml)
            fetch_resp.raise_for_status()
            ftp_url = find_between(fetch_resp.text, '<PCT-Download-URL_url>', '</PCT-Download-URL_url>')
            assert len(ftp_url) > 0
            download_file(ftp_url, tmpfile)
            logger.info(f"fetched!")
            break
        except (HTTPError, AssertionError, IndexError) as e:
            logger.info(f"fetching failed: {e}")
            logger.info(f"retry after: {retry_interval}, total time cost: {time_counter}/{total_time_limit}")
            time.sleep(retry_interval)
            time_counter += retry_interval

    # read downloaded file
    with open(tmpfile, 'r') as f:
        lines = f.readlines()
    result_mapping = dict()
    for line in lines:
        items = line.strip().split()
        if len(items) == 0:
            continue
        elif input_type == 'cid':
            items[0] = int(items[0])

        if len(items) == 1:
            result_mapping[items[0]] = None
        elif len(items) == 2:
            result_mapping[items[0]] = items[1]
        else:
            raise ValueError(f"funny line: {line}")
    removefile(tmpfile)
    return result_mapping


def identify_compound(identifier: Union[str, int], input_type: str) -> Compound:
    """
    use `fastidentity` of pug rest, one per request, not suitable for bulk identification

    :param identifier: string or int (cid)
    :param input_type: 'smiles', 'cid', 'inchi'
    :return:
    """
    if input_type == 'inchi':
        smi = inchi2smiles(identifier)
        input_type = 'smiles'
        identifier = smi

    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastidentity/{input_type}/{identifier}/property/InChI,CanonicalSMILES,IUPACName/json"
    url += "?identity_type=same_stereo_isotope"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    entries = data['PropertyTable']['Properties']
    if len(entries) > 1:
        logger.warning(f'fast identity returning multiple entries: {len(entries)}')
    entry = entries[0]
    cid = entry["CID"]
    smi = entry["CanonicalSMILES"]
    inchi = entry["InChI"]
    name = entry["IUPACName"]
    return Compound(cid, smi, inchi, name)


def identify_compounds(identifiers: Union[list[str], list[int]], input_type: str = 'smiles', ) -> dict[str, Compound]:
    """
    use pug, suitable for bulk identifications

    :param input_type: 'smiles', 'cid', 'inchi'
    :return:
    """
    identifier_dicts = []
    output_types = ['cid', 'inchi', 'iupac', 'smiles']
    for output_type in output_types:
        d = request_convert_identifiers(identifiers, input_type, output_type)
        identifier_dicts.append(d)

    dd = defaultdict(dict)
    for d, iname in zip(identifier_dicts, output_types):
        for key, value in d.items():
            dd[key][iname] = value
    compound_dict = dict()
    for input_identifier in dd:
        try:
            assert dd[input_identifier]['cid'] is not None
        except AssertionError:
            logger.warning(f'identifier failed with input identifier/type: {input_identifier}{input_type}')
            continue
        c = Compound.from_dict(dd[input_identifier])
        compound_dict[input_identifier] = c
    return compound_dict
