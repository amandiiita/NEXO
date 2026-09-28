import json
from tools import (
    search_calendar_events,
    search_services,
    enrich_services_with_history
)
from ranking import (
    calculate_event_score,
    calculate_service_score
)

RISK_KEYWORDS = [
    "me siento muy mal", "me siento mal", "crisis", "no puedo más", "no puedo mas",
    "angustia", "ansiedad", "deprimid", "llorar", "necesito ayuda", "hablar con alguien",
    "colaps", "solo y mal", "salud mental", "terapia", "orientación psicológica"
]

DISTRICT_ALIASES = {
    "gaia": "DIST_GAIA", "dist_gaia": "DIST_GAIA",
    "nebula": "DIST_NEBULA", "nébula": "DIST_NEBULA", "dist_nebula": "DIST_NEBULA",
    "vector": "DIST_VECTOR", "dist_vector": "DIST_VECTOR",
    "horizon": "DIST_HORIZON", "horizonte": "DIST_HORIZON", "dist_horizon": "DIST_HORIZON",
    "quantum": "DIST_QUANTUM", "dist_quantum": "DIST_QUANTUM",
}

INSTITUTION_ALIASES = {
    "nova": "UNI_NOVA_AETHER", "nova aether": "UNI_NOVA_AETHER", "uni_nova_aether": "UNI_NOVA_AETHER",
    "nexus": "INST_NEXUS", "inst_nexus": "INST_NEXUS",
    "horizonte": "UNI_HORIZONTE", "uni_horizonte": "UNI_HORIZONTE",
}


def extract_context_from_text(text, current_context, api_key=None):
    t = text.lower()
    updated = current_context.copy()

    # 1. Reglas deterministas de seguridad e intención
    if any(k in t for k in RISK_KEYWORDS):
        updated["goal"] = "human_support"
    elif any(k in t for k in ["conocer gente", "amigos", "participar", "actividades", "integrar", "conectar", "club", "pares", "poco tiempo"]):
        if updated.get("goal") != "human_support":
            updated["goal"] = "social_connection"

    if any(k in t for k in ["18:00", "18 hrs", "después de las 18", "tarde", "trabajo", "trabajar", "25 horas", "20 horas", "poco tiempo", "sábado", "sabado", "fin de semana", "sí", "si"]):
        updated["after_18h_or_weekend"] = True
        updated["availability_confirmed"] = True
    elif any(k in t for k in ["cualquier horario", "tengo tiempo", "no trabajo", "mañana", "todo el día"]):
        updated["after_18h_or_weekend"] = False
        updated["availability_confirmed"] = True

    for alias, code in sorted(DISTRICT_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in t:
            if alias == "horizonte" and ("uni" in t or "estud" in t):
                continue
            updated["district_id"] = code
            break

    for alias, code in sorted(INSTITUTION_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in t:
            updated["institution_id"] = code
            break

    # 2. Interpretación estructurada con Gemini LLM (si la API Key está activa)
    if api_key and api_key.strip():
        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            prompt = f"""
            Eres el intérprete semántico del agente NEXO en Ciudad Aethera.
            Mensaje del estudiante: "{text}"
            Contexto previo: {json.dumps(updated)}
            Devuelve ÚNICAMENTE un JSON válido con estas claves exactas:
            {{
              "goal": "social_connection" o "human_support",
              "district_id": "DIST_GAIA", "DIST_NEBULA", "DIST_VECTOR", "DIST_HORIZON", "DIST_QUANTUM" o null,
              "institution_id": "UNI_NOVA_AETHER", "INST_NEXUS", "UNI_HORIZONTE" o null,
              "after_18h_or_weekend": true o false,
              "interpreted_need": "resumen de 1 frase de la necesidad y restricciones del estudiante"
            }}
            Regla crítica: si expresa angustia severa, crisis o pide ayuda emocional, "goal" DEBE ser "human_support".
            """
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            llm_data = json.loads(raw)
            if llm_data.get("goal") == "human_support":
                updated["goal"] = "human_support"
            if llm_data.get("district_id") and not updated.get("district_id"):
                updated["district_id"] = llm_data["district_id"]
            if llm_data.get("institution_id") and not updated.get("institution_id"):
                updated["institution_id"] = llm_data["institution_id"]
            if llm_data.get("interpreted_need"):
                updated["llm_interpreted_need"] = llm_data["interpreted_need"]
        except Exception:
            pass

    return updated


def generate_grounded_explanation(student_context, top_services, top_events, api_key=None):
    """
    Si hay API Key de Gemini, redacta una recomendación personalizada usando
    EXCLUSIVAMENTE los resultados reales de D6, D7 y D2 (cero alucinación).
    """
    default_msg = (
        f"Encontré y prioricé estas oportunidades reales del Data Pack compatibles con tu "
        f"disponibilidad {'extendida (>18:00 / sábado)' if student_context.get('after_18h_or_weekend') else 'general'}, "
        f"tu ubicación en {student_context['district_id']} y tu institución ({student_context['institution_id']}):"
    )
    if not api_key or not api_key.strip():
        return default_msg

    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        prompt = f"""
        Eres NEXO, un agente logístico de integración universitaria en Ciudad Aethera.
        No simules ser psicólogo ni inventes datos.
        Contexto del estudiante: {json.dumps(student_context)}
        Mejor espacio en D6: {json.dumps(top_services[0] if top_services else {})}
        Mejores eventos en D7: {json.dumps(top_events[:2] if top_events else [])}
        Redacta en 3 líneas claras y cercanas por qué priorizaste estas opciones específicas para sus restricciones,
        mencionando sus nombres exactos, horarios/fechas y puntajes de compatibilidad.
        """
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return resp.text.strip()
    except Exception:
        return default_msg


def run_nexo(calendar, services, support_history, student_context, api_key=None):
    goal = student_context.get("goal") or "social_connection"
    district_id = student_context.get("district_id")
    institution_id = student_context.get("institution_id")

    # CASO 2: DERIVACIÓN HUMANA (D6 + D2)
    if goal == "human_support":
        if not district_id:
            return {
                "status": "needs_info",
                "missing_field": "district_id",
                "agent_message": (
                    "No puedo evaluar ni diagnosticar cómo te sientes, pero sí puedo ayudarte "
                    "a encontrar apoyo humano disponible. ¿En qué distrito te encuentras "
                    "(Nebula, Gaia, Vector, Horizon o Quantum)?"
                ),
                "context": student_context
            }

        support_spaces = services[
            (services["district_id"] == district_id)
            & (services["service_type"].isin(["counseling", "peer_support"]))
        ].copy()
        support_spaces = enrich_services_with_history(support_spaces, support_history)

        referrals = []
        for _, row in support_spaces.iterrows():
            referrals.append({
                "service_id": row["service_id"],
                "name": row["name"],
                "service_type": row["service_type"],
                "district_id": row["district_id"],
                "schedule": row["schedule"],
                "channels": row["channels"],
                "average_wait_days": row["average_wait_days"],
                "median_wait_days": row["median_wait_days"],
                "attendance_rate": row["attendance_rate"],
                "referral_information": row["referral_information"]
            })

        return {
            "status": "referral_ready",
            "agent_message": (
                "No puedo evaluar ni diagnosticar tu situación. Sí puedo conectarte directamente "
                f"con los servicios de orientación profesional y apoyo entre pares disponibles en {district_id}:"
            ),
            "tools_used": ["search_services(D6)", "enrich_services_with_history(D2)"],
            "referrals": referrals,
            "context": student_context
        }

    # CASO 1: PREGUNTAR LO QUE FALTA
    if not student_context.get("availability_confirmed"):
        return {
            "status": "needs_info",
            "missing_field": "availability",
            "agent_message": (
                "Entiendo. Para priorizar opciones compatibles con tu disponibilidad, "
                "¿generalmente puedes participar después de las 18:00 o los fines de semana?"
            ),
            "context": student_context
        }

    if not district_id:
        return {
            "status": "needs_info",
            "missing_field": "district_id",
            "agent_message": (
                "Perfecto. Para buscar opciones cercanas a ti, ¿en qué distrito te mueves "
                "principalmente? (Nebula, Gaia, Vector, Horizon o Quantum)"
            ),
            "context": student_context
        }

    if not institution_id:
        return {
            "status": "needs_info",
            "missing_field": "institution_id",
            "agent_message": (
                "¡Gracias! Por último, ¿en qué institución estudias? "
                "(Nova Aether, Instituto Nexus o Universidad Horizonte)"
            ),
            "context": student_context
        }

    # EJECUTAR HERRAMIENTAS Y RANKING (D7 + D6 + D2)
    events = search_calendar_events(calendar, institution_id, district_id)
    evaluation_periods = calendar[
        (calendar["period_id"] == "PER_2026_4")
        & (calendar["event_type"] == "evaluation_week")
    ].copy()

    ranked_events = []
    for _, event in events.iterrows():
        score, reasons = calculate_event_score(event, student_context, evaluation_periods)
        ranked_events.append({
            "id": event["calendar_event_id"],
            "title": event["title"],
            "event_type": event["event_type"],
            "start_date": event["start_date"],
            "end_date": event["end_date"],
            "institution_id": event["institution_id"],
            "district_id": event["district_id"],
            "score": score,
            "reasons": reasons
        })

    peer_services = search_services(services, district_id=district_id, service_type="peer_support")
    peer_services = enrich_services_with_history(peer_services, support_history)

    ranked_services = []
    for _, service in peer_services.iterrows():
        score, reasons = calculate_service_score(service, student_context)
        ranked_services.append({
            "id": service["service_id"],
            "name": service["name"],
            "service_type": service["service_type"],
            "district_id": service["district_id"],
            "schedule": service["schedule"],
            "channels": service["channels"],
            "capacity": service["capacity"],
            "average_wait_days": service["average_wait_days"],
            "attendance_rate": service["attendance_rate"],
            "score": score,
            "reasons": reasons
        })

    ranked_events = sorted(ranked_events, key=lambda x: x["score"], reverse=True)[:3]
    ranked_services = sorted(ranked_services, key=lambda x: x["score"], reverse=True)[:2]

    explanation_msg = generate_grounded_explanation(
        student_context, ranked_services, ranked_events, api_key
    )

    return {
        "status": "recommendations_ready",
        "agent_message": explanation_msg,
        "tools_used": [
            "search_calendar_events(D7)",
            "search_services(D6)",
            "enrich_services_with_history(D2)",
            "calculate_event_score & calculate_service_score"
        ],
        "events": ranked_events,
        "peer_services": ranked_services,
        "context": student_context
    }
