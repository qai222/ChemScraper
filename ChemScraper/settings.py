"""
global variables
"""

# chemical identifier with the highest priority
MainIdentifierType = "cid"

# identifiers that can be used for chemicals
KnownIdentifierTypes = ('smiles', 'cid', 'inchi')

# `SourceName` defined in pubchem Entrez system, a complete list can be found at
# https://pubchem.ncbi.nlm.nih.gov/sources/
VendorSources = (
    'Sigma-Aldrich',
    'Thermo Fisher Scientific',
)

# default rng seed
SEED = 42
