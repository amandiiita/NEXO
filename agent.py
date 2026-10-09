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

    # 1. Reglas deterministas ultrarrápidas
    t_clean = t.strip().replace(".", "").replace(",", "")
    
    # El saludo lo atrapamos aquí para que sea instantáneo
    if t_clean in ["hola", "holi", "buenos días", "buenos dias", "buenas tardes", "buenas noches", "buenas", "qué tal", "que tal", "hola nexo", "hello", "holis"]:
        updated["goal"] = "greeting"
        return updated
        
    if any(k in t for k in RISK_KEYWORDS):
        updated["goal"] = "human_support"

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

    # 2. Interpretación Semántica Estructural con Gemini (A prueba de balas)
    if api_key and api_key.strip():
        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            prompt = f"""
            Analiza este mensaje del usuario: "{text}"
            
            Tu ÚNICA tarea es devolver un objeto JSON válido con la clasificación de la intención del usuario.
            
            OPCIONES OBLIGATORIAS PARA LA CLAVE "goal":
            - "human_support": Si expresa sentirse mal, triste, en crisis o necesita ayuda psicológica.
            - "out_of_context": Si pide un chiste, una receta de cocina, o habla de CUALQUIER tema que NO sea vida universitaria.
            - "social_connection": Si busca actividades, eventos, conocer gente o integrarse a la universidad.
            
            Devuelve EXACTAMENTE este formato JSON (sin texto adicional, sin comillas invertidas de markdown):
            {{
              "goal": "Escribe_Aqui_La_Opcion_Elegida",
              "interpreted_need": "Breve resumen de lo que pidió el usuario"
            }}
            """
            # AQUÍ ACTUALIZAMOS A LA VERSIÓN 3.8
            resp = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
            
            # Limpieza exhaustiva para que el JSON no rompa el código
            raw = resp.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            
            llm_data = json.loads(raw)
            
            new_goal = llm_data.get("goal")
            # Solo actualizamos el goal si Gemini nos dio una de las 3 opciones válidas
            if new_goal in ["human_support", "out_of_context", "social_connection"]:
                updated["goal"] = new_goal
                
            if llm_data.get("interpreted_need"):
                updated["llm_interpreted_need"] = llm_data["interpreted_need"]
                
        except Exception as e:
            # Si Gemini falla, te lo avisará en la terminal negra de tu compu
            print(f"⚠️ Error leyendo a Gemini: {e}")
            pass

    # Fallback de seguridad por si falla el internet o la API
    if not updated.get("goal"):
        updated["goal"] = "social_connection"

    return updated


def generate_grounded_explanation(student_context, top_services, top_events, api_key=None):
    default_msg = (
        f"Encontré y prioricé estas oportunidades reales del Data Pack compatibles con tu "
        f"disponibilidad {'extendida (>18:00 / sábado)' if student_context.get('after_18h_or_weekend') else 'general'}, "
        f"tu ubicación en {student_context.get('district_id', 'tu distrito')} y tu institución ({student_context.get('institution_id', 'tu universidad')}):"
    )
    if not api_key or not api_key.strip():
        return default_msg

    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        prompt = f"""
        Eres NEXO, un agente logístico de integración universitaria en Ciudad Aethera.
        Contexto del estudiante: {json.dumps(student_context)}
        Mejor espacio en D6: {json.dumps(top_services[0] if top_services else {})}
        Mejores eventos en D7: {json.dumps(top_events[:2] if top_events else [])}
        Redacta en 3 líneas claras y cercanas por qué priorizaste estas opciones específicas.
        """
        # AQUÍ ACTUALIZAMOS A LA VERSIÓN 3.8
        resp = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
        return resp.text.strip()
    except Exception:
        return default_msg


def run_nexo(calendar, services, support_history, student_context, api_key=None):
    goal = student_context.get("goal")
    
    # --- CASO 0: GUARDRAILS ESTRUCTURALES ---
    if goal == "greeting":
        student_context["goal"] = None # Reseteamos para el próximo turno
        return {
            "status": "greeting",
            "agent_message": "Hola, soy NEXO, tu asistente de integración. ¿En qué te ayudo?",
            "context": student_context
        }
        
    if goal == "out_of_context":
        student_context["goal"] = None # Reseteamos para el próximo turno
        return {
            "status": "out_of_context",
            "agent_message": "Lo siento, solo puedo ayudarte con tu integración universitaria y servicios del campus.",
            "context": student_context
        }

    goal = goal or "social_connection"
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