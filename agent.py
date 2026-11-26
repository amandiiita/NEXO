"""Herramientas institucionales. No se interpretan contactos ni cupos a partir de D2."""
from entorno import comprobar
comprobar()
from ranking import calculate_event_score, calculate_service_score
from tools import search_calendar_events, search_services, enrich_services_with_history


def calendario_ordenado(calendar, context):
    events = search_calendar_events(calendar, context["institution_id"], context["district_id"])
    exams = calendar[(calendar.period_id == "PER_2026_4") & (calendar.event_type == "evaluation_week")]
    records = []
    for row in events.to_dict("records"):
        score, reasons = calculate_event_score(row, context, exams)
        records.append({**row, "id": row["calendar_event_id"], "score": score, "reasons": reasons})
    return sorted(records, key=lambda row: -row["score"])


def espacios_ordenados(services, history, context, apoyo):
    if apoyo:
        eligible = services[services.district_id.eq(context["district_id"]) &
                            services.service_type.isin(["counseling", "peer_support"])]
    else:
        eligible = search_services(services, district_id=context["district_id"], service_type="peer_support")
        eligible = eligible[eligible.district_id.eq(context["district_id"])]
    records = enrich_services_with_history(eligible, history).to_dict("records")
    for row in records:
        row["id"] = row["service_id"]
        if not apoyo:
            row["score"], row["reasons"] = calculate_service_score(row, context)
    if apoyo:
        return sorted(records, key=lambda row: row["service_type"] != "counseling")
    return sorted(records, key=lambda row: -row["score"])


def run_nexo(calendar, services, support_history, student_context, api_key=None):
    """La búsqueda es de solo lectura. El cliente oficial invoca solo la colección necesaria."""
    ctx = student_context
    goal = ctx.get("goal")
    if goal in ("greeting", "out_of_context"):
        return {"status":goal, "context":ctx, "agent_message":"Soy NEXO, agente de integración universitaria."}
    apoyo = goal == "human_support"
    required = ("district_id",) if apoyo else ("availability_confirmed", "district_id", "institution_id")
    for field in required:
        if not ctx.get(field):
            return {"status":"needs_info", "missing_field":"availability" if field == "availability_confirmed" else field,
                    "context":ctx, "agent_message":"Falta un dato para buscar opciones compatibles."}
    if apoyo:
        return {"status":"referral_ready", "context":ctx, "referrals":espacios_ordenados(services, support_history, ctx, True),
                "tools_used":["filtrar_orientacion(D6)", "agregar_historial(D2)"], "agent_message":"Orientación institucional."}
    kind = ctx.get("consulta", "ambas")
    used = []
    events, peers = [], []
    if kind in ("events", "ambas"):
        events = calendario_ordenado(calendar, ctx)
        used += ["search_calendar_events(D7)", "calculate_event_score(D7)"]
    if kind in ("peers", "ambas"):
        peers = espacios_ordenados(services, support_history, ctx, False)
        used += ["search_services(D6)", "enrich_services_with_history(D2)", "calculate_service_score(D6)"]
    return {"status":"recommendations_ready", "context":ctx, "tools_used":used, "events":events,
            "peer_services":peers, "agent_message":"Resultados del catálogo ordenados según tus preferencias."}

