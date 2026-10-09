from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def load_calendar():
    path = DATA_DIR / "D7_calendar.csv"
    return pd.read_csv(path)

def load_support_history():
    path = DATA_DIR / "D2_support_services.csv"
    return pd.read_csv(path)

def load_services_map():
    path = DATA_DIR / "D6_services_map.geojson"
    with open(path, "r", encoding="utf-8") as f:
        geo = json.load(f)
    rows = []
    for feat in geo["features"]:
        props = feat["properties"].copy()
        coords = feat["geometry"]["coordinates"]
        props["lon"] = coords[0]
        props["lat"] = coords[1]
        props["channels"] = ", ".join(props.get("channels", []))
        rows.append(props)
    return pd.DataFrame(rows)

def load_all_data():
    calendar = load_calendar()
    support_history = load_support_history()
    services = load_services_map()
    return calendar, support_history, services
