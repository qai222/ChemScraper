import pandas as pd
from pandas._typing import FilePath
import os
import glob
from collections import defaultdict
import re


def pool(suggestion_csv: FilePath, folder: FilePath):

    label_to_vendor_record = defaultdict(dict)
    for result_csv in glob.glob(f"{folder}/*.csv"):
        result_csv_name = os.path.basename(result_csv)[:-4]
        result_csv_name, vendor = result_csv_name.split('.')
        label, cas = result_csv_name.split('--')
        df = pd.read_csv(result_csv)
        df = df[[c for c in df.columns if 'unnamed' not in c.lower()]]

        r = df.to_dict(orient='records')[0]
        if vendor == 'sigma':
            packsize = r['Pack Size']
            price = r['Price']
            avail = r['Availability']
            avail = re.sub("[\(\[].*?[\)\]]", "", avail)
            url = r['url']
        else:
            packsize = r['Quantity']
            price = r['Price']
            avail = r['Availability']
            url = r['product_url']

        vendor_record = {
            f'{vendor}-price': f"{price}/{packsize}",
            f'{vendor}-avail': avail,
            f'{vendor}-url': url,
        }
        label_to_vendor_record[label].update(vendor_record)

    df_suggest = pd.read_csv(suggestion_csv)
    final_records = []
    icluster = 0
    for r in df_suggest.to_dict(orient='records'):
        label = r['ligand_label']
        if pd.isna(label):
            icluster += 1
            continue
        else:
            fr = dict()
            fr.update(r)
            fr['cluster'] = icluster
            fr.update(label_to_vendor_record[label])
        final_records.append(fr)
    return pd.DataFrame.from_records(final_records)


df = pool("suggestion__std_top2%mu__feature__top.csv", "vendor_std_top2%mu__feature_top")
df.to_csv('vendor_std_top2%mu__feature__top.csv', index=False)

df = pool("suggestion__mu_top2%mu__feature__top.csv", "vendor_mu_top2%mu__feature__top")
df.to_csv('vendor_mu_top2%mu__feature__top.csv', index=False)

df = pool("suggestion__std__feature__top.csv", "vendor_std__feature__top")
df.to_csv('vendor_std__feature__top.csv', index=False)

df = pool("suggestion__mu_top2%mu__feature__bottom.csv", "vendor_mu_top2%mu__feature__bottom")
df.to_csv('vendor_mu_top2%mu__feature__bottom.csv', index=False)
