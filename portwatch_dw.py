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
            "outFields": "date,portname,transit_calls,trade_value_usd",
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
    df["date"] = pd.to_datetime(df["date"], unit="ms")
    return df

def prepare_data(df):
    last30 = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)]
    agg = (last30.groupby("portname")
           .agg(avg_calls=("transit_calls", "mean"),
                avg_trade=("trade_value_usd", "mean"))
           .reset_index()
           .sort_values("avg_calls", ascending=False))
    return agg

def create_chart():
    payload = {
        "title": f"Colli di bottiglia - transiti medi ultimi 30gg ({datetime.now():%d %b %Y})",
        "type": "d3-bars",
        "metadata": {
            "describe": {
                "intro": "Fonte: IMF PortWatch / AIS satellitare."
            }
        }
    }
    r = requests.post(f"{DW_BASE}/charts", headers=DW_HEADERS, json=payload)
    r.raise_for_status()
    cid = r.json()["id"]
    print(f"Chart creata: {cid}")
    return cid

def upload_data(cid, df):
    r = requests.put(
        f"{DW_BASE}/charts/{cid}/data",
        headers={**DW_HEADERS, "Content-Type": "text/csv"},
        data=df.to_csv(index=False).encode("utf-8")
    )
    r.raise_for_status()
    print("Dati caricati")

def publish_chart(cid):
    r = requests.post(f"{DW_BASE}/charts/{cid}/publish", headers=DW_HEADERS)
    r.raise_for_status()
    print("Pubblicata!")

print("1. Scarico dati PortWatch...")
df_raw = fetch_chokepoints(days=90)
print(f"   {len(df_raw)} record scaricati")
print("2. Aggrego...")
df_map = prepare_data(df_raw)
print(df_map.head())
print("3. Creo chart...")
cid = create_chart()
print("4. Carico dati...")
upload_data(cid, df_map)
print("5. Pubblico...")
publish_chart(cid)
