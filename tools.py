import pandas as pd


def search_calendar_events(calendar, institution_id=None, district_id=None):
    """
    Busca actividades en D7 (PER_2026_4) que pertenezcan a la institución del
    estudiante O a su distrito, para que el ranking las compare y ordene.
    """
    df = calendar.copy()
    df = df[df["period_id"] == "PER_2026_4"]
    df = df[df["event_type"].isin(["university_activity", "wellbeing_activity"])]

    if institution_id and district_id:
        df = df[
            (df["institution_id"] == institution_id)
            | (df["institution_id"] == "ALL")
            | (df["district_id"] == district_id)
        ]
    return df


def search_services(services, district_id=None, service_type=None):
    """
    Busca servicios en D6 priorizando el distrito del estudiante y
    manteniendo opciones comparables para el ranking.
    """
    df = services.copy()
    if service_type:
        df = df[df["service_type"] == service_type]
    return df


def enrich_services_with_history(services, support_history):
    """Agrega información histórica real de D2 a los servicios de D6."""
    history = (
        support_history
        .groupby("service_id")
        .agg(
            average_wait_days=("wait_days", "mean"),
            median_wait_days=("wait_days", "median"),
            attendance_rate=("attended", "mean")
        )
        .reset_index()
    )
    history["average_wait_days"] = history["average_wait_days"].round(1)
    history["median_wait_days"] = history["median_wait_days"].round(0)
    history["attendance_rate"] = (history["attendance_rate"] * 100).round(1)

    return services.merge(history, on="service_id", how="left")
