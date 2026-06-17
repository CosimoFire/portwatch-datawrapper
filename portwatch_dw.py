import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta

DW_TOKEN = os.environ["DW_TOKEN"]
DW_BASE = "https://api.datawrapper.de/v3"
DW_HEADERS = {
    "Authorization": f"Bearer {DW_TOKEN}",
    "Content-Type": "application/json"
}

ARCGIS = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG"
    "/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
)

def fetch_chokepoints(days=90):
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    records = []
    offset = 0
    while True:
        p = {
            "where": f"date >= {cutoff}",
            "outFields": "*",
            "resultOffset": offset,
            "resultRecordCount": 2000,
            "orderByFields": "date",
            "f": "json"
        }
        r = requests.get(ARCGIS, params=p).json()
        features = r.get("features", [])
        if not features:
            break
        records.extend(f["attributes"] for f in features)
        offset += 2000
        time.sleep(0.3)
    df = pd.DataFrame(records)
    print("COLONNE:", df.columns.tolist())
    print(df.head(2))
    return df

print("1. Scarico dati PortWatch...")
df_raw = fetch_chokepoints(days=90)
print(f"   {len(df_raw)} record scaricati")
