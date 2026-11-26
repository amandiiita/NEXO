from pathlib import Path
import json
from entorno import comprobar
comprobar()
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
    schemas = (
        (calendar, {"calendar_event_id", "period_id", "event_type", "title", "start_date",
                    "end_date", "institution_id", "district_id"}),
        (support_history, {"service_id", "wait_days", "attended"}),
        (services, {"service_id", "name", "service_type", "district_id", "schedule",
                    "channels", "capacity", "referral_information"}),
    )
    if any(not fields.issubset(table.columns) for table, fields in schemas):
        raise ValueError("Faltan columnas requeridas en el catálogo de Aethera")
    for table, key in ((services, "service_id"), (calendar, "calendar_event_id")):
        if table[key].isna().any() or not table[key].is_unique:
            raise ValueError(f"El catálogo contiene identificadores inválidos en {key}")
    for column in ("start_date", "end_date"):
        pd.to_datetime(calendar[column], format="%Y-%m-%d", errors="raise")
        if calendar[column].isna().any():
            raise ValueError("Hay fechas incompletas en el calendario")
    if (calendar["end_date"] < calendar["start_date"]).any():
        raise ValueError("El calendario contiene rangos invertidos")
    return calendar, support_history, services
