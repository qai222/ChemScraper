ChemScraper
---
Scraping chemical vendors for pricing/availability info.
### dependencies
`pip install -r requirements.txt`

### usage
```python
from ChemScraper import *
browser_driver = get_chrome_driver()
compound = identify_compound('C(CN)N', 'smiles')
cas_number = get_cas_number(compound.cid)
df_pa = get_sigma_aldrich_patables(browser_driver, cas_number)[['SKU', 'Availability', 'Price']]
df_pa.to_csv("dfpa.csv", index=False)
```
This writes out a csv:
```csv
SKU,Availability,Price
E26266-5ML,"Available to ship on August 08, 2022 Details...",$36.20
E26266-100ML,"Available to ship on August 08, 2022 Details...",$47.70
E26266-1L,"Available to ship on August 08, 2022 Details...",$60.70
E26266-2.5L,"Available to ship on August 08, 2022 Details...",$141.00
E26266-4X100ML,"Available to ship on August 08, 2022 Details...",$147.00
03550-250ML,"Available to ship on August 08, 2022 Details...",$70.70
...
```

### todo
- [ ] simplify `requirements.txt`