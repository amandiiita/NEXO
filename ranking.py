import pandas as pd

DISTRICT_NAMES = {
    "DIST_GAIA": "Distrito Gaia",
    "DIST_NEBULA": "Distrito Nébula",
    "DIST_VECTOR": "Distrito Vector",
    "DIST_HORIZON": "Distrito Horizonte",
    "DIST_QUANTUM": "Distrito Quantum",
    "ALL": "Todos los distritos"
}

INSTITUTION_NAMES = {
    "UNI_NOVA_AETHER": "Universidad Nova Aether",
    "INST_NEXUS": "Instituto Nexus",
    "UNI_HORIZONTE": "Universidad Horizonte",
    "ALL": "Abierto a todas las instituciones"
}


def calculate_event_score(event, student_context, evaluation_periods):
    """Calcula la compatibilidad de una actividad de D7 con explicaciones en español."""
    score = 0
    reasons = []

    student_district = student_context.get("district_id")
    student_institution = student_context.get("institution_id")

    dist_label = DISTRICT_NAMES.get(student_district, student_district)
    inst_label = INSTITUTION_NAMES.get(student_institution, student_institution)

    # 1. DISTRITO — máximo 30 puntos
    if event["district_id"] == student_district:
        score += 30
        reasons.append(f"Se realiza en tu misma zona ({dist_label})")
    elif event["district_id"] == "ALL":
        score += 15
        reasons.append("Actividad abierta para todos los distritos de la ciudad")
    else:
        other_dist = DISTRICT_NAMES.get(event["district_id"], event["district_id"])
        score += 5
        reasons.append(f"Se realiza en otro sector ({other_dist})")

    # 2. INSTITUCIÓN — máximo 20 puntos
    if event["institution_id"] == student_institution:
        score += 20
        reasons.append(f"Organizado directamente por tu institución ({inst_label})")
    elif event["institution_id"] == "ALL":
        score += 15
        reasons.append("Encuentro interuniversitario abierto a toda la comunidad")

    # 3. EVALUACIONES — máximo 15 puntos (cruce real de fechas en D7)
    if not evaluation_periods.empty:
        event_start = pd.to_datetime(event["start_date"])
        event_end = pd.to_datetime(event["end_date"])
        conflict = False

        for _, period in evaluation_periods.iterrows():
            period_start = pd.to_datetime(period["start_date"])
            period_end = pd.to_datetime(period["end_date"])
            if event_start <= period_end and event_end >= period_start:
                conflict = True
                break

        if not conflict:
            score += 15
            reasons.append("No choca con tus semanas de exámenes en el calendario")

    return score, reasons


def calculate_service_score(service, student_context):
    """Calcula la compatibilidad de un espacio de D6 con explicaciones limpias."""
    score = 0
    reasons = []

    student_district = student_context.get("district_id")
    late_or_weekend = student_context.get("after_18h_or_weekend", False)
    dist_label = DISTRICT_NAMES.get(student_district, student_district)

    # 1. DISTRITO — 30 puntos
    if service["district_id"] == student_district:
        score += 30
        reasons.append(f"Queda cerca de ti, dentro de {dist_label}")
    else:
        other_dist = DISTRICT_NAMES.get(service["district_id"], service["district_id"])
        score += 10
        reasons.append(f"Ubicado en {other_dist}")

    # 2. HORARIO — 35 puntos
    schedule = str(service["schedule"])
    if late_or_weekend:
        if "20:00" in schedule or "Sat" in schedule:
            score += 35
            reasons.append("Cuenta con horario vespertino (hasta las 20:00 hrs) y abre los sábados")
        elif "18:00" in schedule:
            score += 10
            reasons.append("Atiende de lunes a viernes hasta las 18:00 hrs")
    else:
        score += 35
        reasons.append("Horario compatible con tu disponibilidad semanal")

    # 3. TIPO DE ESPACIO — 20 puntos
    if service["service_type"] == "peer_support":
        score += 20
        reasons.append("Espacio horizontal diseñado para conocer pares y crear comunidad")

    # 4. CONTINUIDAD — 15 puntos
    score += 15
    reasons.append("Acceso continuo durante todo el semestre sin chocar con evaluaciones")

    return score, reasons
