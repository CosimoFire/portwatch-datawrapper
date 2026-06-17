import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta

# ─── CONFIG ───────────────────────────────────────────────
DW_TOKEN = os.environ["DW_TOKEN"]
DW_BASE  = "https://api.datawrapper.de/v3"
DW_HEADERS = {
    "Authorization": f"Bearer {DW_TOKEN}",
    "Content-Type": "application/json"
}

ARCGIS_BASE = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG"
    "/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
)

# ─── 1. SCARICA DATI PORTWATCH ────────────────────────────
def fetch_chokepoints(days=90):
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    all_records = []
    offset = 0
    while True:
        params = {
            "where": f"date >= {cutoff}",
            "outFields": "date,portname,transit_calls,trade_value_usd",
            "resultOffset": offset,
            "resultRecordCount": 2000,
            "orderByFields": "date",
            "f": "json"
        }
        r = requests.get(ARCGIS_BASE, params=params).json()
        features = r.get("features", [])
        if not features:
            break
        all_records.extend(f["attributes"] for f in features)
        offset += 2000
        time.sleep(0.3)
    df = pd.DataFrame(all_records)
    df["date"] = pd.to_datetime(df["date"], unit="ms")
    return df

# ─── 2. AGGREGA ───────────────────────────────────────────
def prepare_data(df):
    last30 = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)]
    agg = (last30
           .groupby("portname")
           .agg(
               avg_calls=("transit_calls", "mean"),
               avg_trade=("trade_value_usd", "mean")
           )
           .reset_index()
           .sort_values("avg_calls", ascending=False))
    return agg

# ─── 3. CREA CHART DATAWRAPPER ────────────────────────────
def create_chart():
    payload = {
        "title": f"Colli di bottiglia — transiti medi ultimi 30gg ({datetime.now():%d %b %Y})",
        "type": "d3-bars",
        "metadata": {
            "describe": {
                "intro": "Media giornaliera transiti negli ultimi 30 giorni. Fonte: IMF PortWatch / AIS satellitare."
            }
        }
    }
    r = requests.post(f"{DW_BASE}/charts", headers=DW_HEADERS, json=payload)
    r.raise_for_status()
    chart_id = r.json()["id"]
    print(f"Chart creata: {chart_id}")
    return chart_id

def upload_data(chart_id, df):
    csv_str = df.to_csv(index=False)
    r = requests.put(
        f"{DW_BASE}/charts/{chart_id}/data",
        headers={**DW_HEADERS, "Content-Type": "text/csv"},
        data=csv_str.encode("utf-8")
    )
    r.raise_for_status()
    print("Dati caricati")

def publish_chart(chart_id):
    r = requests.post(f"{DW_BASE}/charts/{chart_id}/publish", headers=DW_HEADERS)
    r.raise_for_status()
    url = r.json().get("data", {}).get("publicUrl", "")
    print(f"Pubblicata: {url}")
    return url

# ─── MAIN ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("1. Scarico dati PortWatch...")
    df_raw = fetch_chokepoints(days=90)
    print(f"   {len(df_raw)} record scaricati")

    print("2. Aggrego...")
    df_map = prepare_data(df_raw)
    print(df_map.head())

    print("3. Creo chart...")
    cid =
