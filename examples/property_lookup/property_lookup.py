import glob
import os.path
import random
import time

from loguru import logger
from rdkit.Chem import Descriptors
from rdkit.Chem import MolFromSmiles
from rdkit.Chem import rdMolDescriptors
from tqdm import tqdm

from ChemScraper import get_chrome_driver, json_load, identify_compound, get_sigma_aldrich_properties_from_cas, \
    get_cas_number, get_sigma_aldrich_properties_from_mf, json_dump

browser_driver = get_chrome_driver(headless=True)
unique_smis = json_load("scraper_input.json")

for smi in tqdm(unique_smis):
    logger.info(f"working on: {smi}")
    outfile = f"prop/{smi}.json"
    if os.path.isfile(outfile) and os.path.getsize(outfile) > 0:
        logger.info(f"outfile already exists, skipping for: {smi}")
        continue

    try:
        compound = identify_compound(identifier=smi, input_type="smiles")
        cas = get_cas_number(compound.cid)
        prop = get_sigma_aldrich_properties_from_cas(browser_driver, cas)
    except Exception:
        logger.critical(f"CANNOT find prop using cas for: {smi}")
        mol = MolFromSmiles(smi)
        mw = Descriptors.MolWt(mol)
        mf = rdMolDescriptors.CalcMolFormula(mol)
        logger.warning(f"search prop using molecular formula instead: \nmf = {mf} mw = {mw}")
        prop = get_sigma_aldrich_properties_from_mf(browser_driver, mf)
    prop_data = {
        "smiles": smi,
        "property_dict": prop,
    }
    json_dump(prop_data, f"prop/{smi}.json")
    logger.info(f"properties saved for: {smi}")
    wait_time = 10 + random.random() * 5
    logger.info(f"waiting for: {wait_time}")
    time.sleep(wait_time)
    logger.info("\n")

scraper_output = {}
for jsonfile in glob.glob("prop/*.json"):
    data = json_load(jsonfile)
    scraper_output[data['smiles']] = data['property_dict']

json_dump(scraper_output, "scraper_output.json")
