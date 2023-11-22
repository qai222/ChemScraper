import json
import pprint
import time

from loguru import logger
from rdkit.Chem import Descriptors
from rdkit.Chem import MolFromSmiles
from rdkit.Chem import rdMolDescriptors
from tqdm import tqdm

from ChemScraper import get_chrome_driver, json_load, identify_compound, get_sigma_aldrich_properties_from_cas, \
    get_cas_number, get_sigma_aldrich_properties_from_mf

browser_driver = get_chrome_driver(headless=True)
unique_smis = json_load("network_lv0.json")['unique_molecular_smis']

props = dict()
for smi in tqdm(unique_smis):
    try:
        compound = identify_compound(identifier=smi, input_type="smiles")
        cas = get_cas_number(compound.cid)
        prop = get_sigma_aldrich_properties_from_cas(browser_driver, cas)
    except Exception:
        logger.critical(f"CANNOT find prop using cas for: {smi}")
        mol = MolFromSmiles(smi)
        mw = Descriptors.MolWt(mol)
        mf = rdMolDescriptors.CalcMolFormula(mol)
        logger.warning("search prop using mf instead")
        print(mf, mw)
        prop = get_sigma_aldrich_properties_from_mf(browser_driver, mf)
    props[smi] = prop
    pprint.pp(prop)
    print("=" * 12)
    time.sleep(10)

with open("network_lv0_prop.json", "w") as f:
    json.dump(props, f)
