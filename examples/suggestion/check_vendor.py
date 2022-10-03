import pandas as pd
from loguru import logger
from ast import literal_eval
from ChemScraper import get_chrome_driver, get_sigma_aldrich_patables, get_thermo_fisher_patables_in_search

if __name__ == '__main__':

    df = pd.read_csv('suggestion_std__feature__top.csv')

    driver = get_chrome_driver(headless=True)
    for record in df.to_dict(orient='records'):
        ligand_label = record['ligand_label']
        if pd.isna(ligand_label):
            continue
        cas = literal_eval(record['cas_number'])[0]
        logger.info(f'working on {ligand_label}: {cas}')
        try:
            df_pa = get_sigma_aldrich_patables(driver, cas)
            df_pa.to_csv(f'{cas}.sigma.csv')
        except Exception as e:
            logger.critical('SIGMA FAILED!')
            logger.exception(e)
        try:
            df_price_fisher = get_thermo_fisher_patables_in_search(driver, cas, use_quickview=True, max_results=1)
            df_price_fisher.to_csv(f'{cas}.fisher.csv')
        except Exception as e:
            logger.critical('Fisher FAILED!')
            logger.exception(e)

        break  # comment if running all ligands