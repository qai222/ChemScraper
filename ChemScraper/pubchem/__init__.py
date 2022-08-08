from ChemScraper.pubchem.entrez import download_vendor_compounds
from ChemScraper.pubchem.view import get_vendor_links, get_cas_number
from ChemScraper.pubchem.gateway import request_convert_identifiers, identify_compounds, identify_compound
"""
NCBI requests limits:
No more than 5 requests per second.
No more than 400 requests per minute.
No longer than 300 second running time per minute.
"""
