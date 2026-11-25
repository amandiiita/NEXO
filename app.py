"""Interfaz de NEXO para ejecutar junto al agente y los datos del proyecto."""

from datetime import date
from html import escape
import logging
from math import isfinite
from numbers import Real
import os
import re
import unicodedata
import time

import streamlit as st
from agent import run_nexo
from data_loader import load_all_data
from nexo_model import DEFAULT_MODEL, interpret_turn, validate_turn

st.set_page_config(page_title="NEXO", page_icon="N", layout="wide")

# 2. Inyección de Estilos Adaptativos y Mesh Gradient (Más pronunciado)
st.markdown("""
    <style>
    /* 1. Fondo Adaptativo con "Mesh Gradient" (Aura AI con mayor intensidad) */
    .stApp {
        background-color: var(--background-color);
        background-image: 
            radial-gradient(circle at 0% 0%, rgba(255, 122, 0, 0.12) 0%, transparent 60%),
            radial-gradient(circle at 100% 0%, rgba(67, 97, 238, 0.08) 0%, transparent 60%);
        background-attachment: fixed;
    }

    /* 2. Hacer la barra superior de Streamlit 100% invisible para que el degradado fluya */
    [data-testid="stHeader"], .stApp > header {
        background-color: transparent !important;
        background: transparent !important;
    }
    
    /* Barra lateral con efecto cristal */
    [data-testid="stSidebar"] {
        background-color: transparent !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(150, 150, 150, 0.15);
    }
    
    /* Botones Píldora de Cristal Adaptables */
    div.stButton > button:first-child {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid rgba(150, 150, 150, 0.2);
        border-radius: 100px;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
    }
    
    /* Efecto al pasar el mouse: Resplandor Naranjo de tu equipo */
    div.stButton > button:first-child:hover {
        background-color: transparent;
        color: #FF7A00;
        border-color: #FF7A00;
        box-shadow: 0 0 15px rgba(255, 122, 0, 0.15);
        transform: translateY(-1px);
    }

    /* Input del chat flotante y limpio */
    .stChatInputContainer {
        border-radius: 24px !important;
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(150, 150, 150, 0.15) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Que el texto del chat se adapte */
    .stChatInputContainer textarea {
        color: var(--text-color) !important;
    }

    </style>
""", unsafe_allow_html=True)

# 3. Logo Esfera de IA Centrado (Ahora cambia de color con el tema)
st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 3rem; padding-bottom: 2rem;">
        <!-- Orbe luminoso -->
        <div style="width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, #FF7A00 0%, #FF3D00 100%); box-shadow: 0 0 40px rgba(255, 122, 0, 0.4), inset 0 0 20px rgba(255, 255, 255, 0.2); margin-bottom: 1.5rem;"></div>
        <!-- Título adaptativo (Usa var(--text-color) para cambiar de blanco a negro automático) -->
        <h1 style="font-size: 3.5rem; font-weight: 700; color: var(--text-color); letter-spacing: -0.04em; margin: 0; line-height: 1.1;">NEXO</h1>
        <!-- Subtítulo adaptativo -->
        <p style="font-size: 1.1rem; color: var(--text-color); opacity: 0.7; margin-top: 0.5rem; font-weight: 300;">Encuentra dónde conectar en tu vida universitaria.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.nexo-card {
    max-width: 635px;
    padding: 1rem 1.15rem;
    background: var(--background-color, light-dark(#fff, #26272f));
    color: inherit;
    border: 1px solid rgba(235, 115, 38, .34);
    border-radius: 17px;
    box-shadow: 0 5px 20px rgba(44, 23, 14, .055);
    overflow-wrap: anywhere;
}
.nexo-card .nexo-type { color: var(--text-color); font-size: .84rem; font-weight: 700; margin: 0 0 .26rem; }
.nexo-type::before { content: ''; display: inline-block; width: .62em; height: .62em; border-radius: 50%; background: #ff7400; margin-right: .45em; }
.nexo-card h3 { font-size: clamp(1.23rem, 3.5vw, 1.55rem); line-height: 1.22; margin: 0; padding: 0; }
.nexo-facts { display: flex; flex-wrap: wrap; gap: .55rem 1.35rem; margin: .85rem 0 0; }
.nexo-facts div { min-width: 7rem; }
.nexo-facts dt { font-size: .85rem; opacity: .8; }
.nexo-facts dd { font-size: .96rem; font-weight: 600; margin: .1rem 0 0; }
.nexo-card .nexo-note { font-size: .9rem; margin: .7rem 0 0; }
.nexo-card-details {
    margin-top: .85rem;
    padding-top: .65rem;
    border-top: 1px solid rgba(140, 130, 125, .28);
    font-size: .9rem;
}
.nexo-card-details summary { cursor: pointer; font-weight: 600; }
.nexo-card-details ul { margin: .45rem 0 0; padding-left: 1.25rem; }
.nexo-event {
    max-width: 635px;
    padding: .65rem .85rem;
    border: 1px solid rgba(160, 145, 134, .35);
    border-radius: 12px;
    background: var(--background-color, light-dark(#fff, #26272f));
    overflow-wrap: anywhere;
}
.nexo-event p { margin: .2rem 0 0; font-size: .9rem; }
[data-testid="stChatMessage"] div.stButton > button[kind="primary"]:first-child {
    background: #a74010;
    color: #fff;
    border-color: #a74010;
}
[data-testid="stChatMessage"] div.stButton > button[kind="primary"]:first-child:hover {
    background: #c05019;
    color: #fff;
}
</style>
""", unsafe_allow_html=True)

DISTRICTS = {
    "DIST_NEBULA": "Nébula",
    "DIST_GAIA": "Gaia",
    "DIST_VECTOR": "Vector",
    "DIST_HORIZON": "Horizonte",
    "DIST_QUANTUM": "Quantum",
}
INSTITUTIONS = {
    "UNI_NOVA_AETHER": "Universidad Nova Aether",
    "INST_NEXUS": "Instituto Nexus",
    "UNI_HORIZONTE": "Universidad Horizonte",
}
DEMO_MESSAGES = {
    "Demo Conversacional": "Quiero conocer gente en la universidad, pero trabajo y salgo después de las 18:00.",
    "Demo Integración": "Estudio en Nova Aether, me muevo por Nébula y quiero conocer gente después de las 18:00.",
    "Demo Derivación": "Últimamente me siento muy mal emocionalmente y necesito hablar con alguien en Nébula.",
}
DAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
DATAPACK_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic")
CHANNELS = {"in_person": "Presencial", "phone": "Teléfono", "digital": "Canal digital", "email": "Correo electrónico"}
ALL_DAYS = tuple(range(7))
TIME_OPTIONS = {
    "Después de las 18:00": (ALL_DAYS, 1080, 1440),
    "Solo sábados": ((5,), 0, 1440),
    "Fin de semana": ((5, 6), 0, 1440),
    "Horario flexible": (ALL_DAYS, 0, 1440),
}
SCENARIO_DATE = date(2026, 11, 23)
SPOKEN_HOURS = {word: hour for hour, word in enumerate(
    ("una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce"), 1)}
DAY_PART_SHIFT = {"manana": 0, "tarde": 12, "noche": 12}
# Interpretación de horas en expresiones como «después de las seis de la tarde».
HOUR_WORD = r"\b(a|las|la) (" + "|".join(SPOKEN_HOURS) + r")(?: de la (manana|tarde|noche))?\b"
HOUR = r"([01]?\d|2[0-3])(?::([0-5]\d))?(?![:\d])"
NEGATIVE_TIME = r"\b(?:no puedo|no estoy disponible|no tengo tiempo|no me acomoda)\b"
INTERESTS = {
    "deporte": r"\b(?:deportes?|futbol|volei|basquet\w*|gimnasio)\b",
    "música": r"\b(?:musica|coro|guitarra|cantar)\b",
    "arte": r"\b(?:arte|pintura|teatro|dibujo|danza|baile)\b",
    "voluntariado": r"\b(?:voluntariado|voluntar\w*)\b",
    "lectura": r"\b(?:lectura|literatura|libros)\b",
    "bienestar": r"\b(?:bienestar|autocuidado|pausa|relajacion)\b",
}
LOG = logging.getLogger("nexo")
SUPPORT_PATTERN = re.compile(
    r"\b(?:me siento (?:muy )?mal|crisis|angustia|ansiedad|deprimid[oa]|hablar con alguien|"
    r"salud mental|orientacion psicologica|apoyo emocional|apoyo humano|no puedo mas|terapia)\b")
AI_PAUSE_SECONDS = 45
AI_FAILURE_REASONS = {
    "timeout": "se agotó el tiempo de espera",
    "quota": "límite de solicitudes",
    "credentials": "credencial rechazada",
    "model_missing": "modelo fuera de alcance",
    "sdk_missing": "componente de Gemini ausente",
    "invalid_response": "respuesta fuera del formato esperado",
    "busy": "conexión ocupada",
    "unavailable": "servicio no disponible",
}
# El modelo elige un estilo. Las frases admisibles conservan todos los datos
# y las restricciones de la respuesta local.
RESPONSE_VARIANTS = {
    "¿Cuándo puedes participar? Puedes decirme el día o el horario que te acomoda.": (
        "¿Qué día o a qué hora te acomoda participar?",
        "Para encontrar algo que puedas aprovechar, dime qué día u horario te sirve."),
    "¿En qué distrito te mueves normalmente?": (
        "¿Por qué distrito te mueves normalmente?", "¿En qué distrito quieres que busque primero?"),
    "¿En qué institución estudias?": (
        "¿Dónde estudias?", "Dime en qué institución estudias para completar la búsqueda."),
    "Empezaría por este espacio en ": (
        "Te propongo partir por este espacio en ", "La primera opción de la búsqueda está en "),
    "También encontré esta opción en ": (
        "Otra opción que puedes revisar está en ", "Para comparar, tienes esta otra opción en "),
    "Podemos retomar este espacio.": (
        "Volvamos a este espacio.", "Esta es la opción de pares que ya habíamos encontrado."),
    "Estas actividades figuran en el calendario del escenario al ": (
        "Estas son las actividades del calendario simulado al ",
        "Puedes revisar estas actividades registradas en el calendario simulado al "),
    "El horario publicado de ": ("Según el catálogo, el horario de ", "El horario que puedes usar como referencia para "),
    "Estos son los criterios que usé para mostrar ": ("Te cuento por qué te mostré ", "Estos criterios explican por qué te mostré "),
    "Estos son los datos de atención que figuran en el catálogo.": (
        "Así figura la atención de este espacio en el catálogo.", "Empieza por estos datos de atención del catálogo."),
    "Puedes confirmar los detalles con quien organiza la actividad.": (
        "Puedes pedir más detalles a quien organiza la actividad.", "Para dar el siguiente paso, consulta con quien organiza la actividad."),
    "Aquí está la información registrada en el calendario de Aethera.": (
        "Esto es lo que figura en el calendario de Aethera.", "Revisa los datos publicados en el calendario de Aethera."),
    "Guardé tu próximo paso durante esta sesión.": (
        "Tu próximo paso quedó guardado durante esta sesión.", "Guardé este plan durante la sesión para que puedas retomarlo."),
    "No encontré espacios de pares compatibles en ": (
        "Con ese filtro, no encontré espacios de pares compatibles en ",
        "El horario indicado dejó sin coincidencias de pares la búsqueda en "),
    "Esa consulta está fuera del ámbito de NEXO.": (
        "Esa consulta queda fuera de lo que cubre NEXO.", "Mi ayuda se limita a la integración universitaria."),
}


@st.cache_data(show_spinner=False)
def catalog():
    return load_all_data()


def setting(name, default=""):
    if name in os.environ:
        return os.environ[name].strip()
    try:
        return str(st.secrets.get(name, default) or default).strip()
    except (FileNotFoundError, ValueError):
        return default


def new_conversation():
    previous = st.session_state.get("nexo") or {}
    st.session_state.nexo = {
        "context": {
            "goal": None, "district_id": None, "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False,
        },
        "availability": None,
        "time_label": None,
        "messages": [],
        "waiting": None,
        "result": None,
        "selected": None,
        "saved": None,
        "time_choices": (),
        "scope_pending": False,
        "search_kind": "peers",
        "interest": None,
        "interest_pending": False,
        "interpretation": "Por iniciar",
        "sources": (),
        "result_key": None,
        "ai_failures": previous.get("ai_failures", 0),
        "ai_backoff_until": previous.get("ai_backoff_until", 0.0),
        "ai_style": None,
        "ai_output": "Redacción verificada de NEXO",
    }


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower().strip()) if not unicodedata.combining(c))


def district_name(code):
    return DISTRICTS.get(code, "Toda Ciudad Aethera" if code == "ALL" else "Por confirmar")


def institution_name(code):
    return INSTITUTIONS.get(code, "Interuniversitaria" if code == "ALL" else "Por confirmar")


def minutes(hour, minute=0):
    return int(hour) * 60 + int(minute)


def clock(value):
    return f"{value // 60:02d}:{value % 60:02d}"


def availability_label(days, start, end):
    day_label = ", ".join(DAYS[day] for day in days) if days != ALL_DAYS else ""
    if start + 1 == end:
        hours = f"a las {clock(start)}"
    elif start and end != 1440:
        hours = f"{clock(start)} a {clock(end)}"
    elif start:
        hours = f"desde las {clock(start)}"
    elif end != 1440:
        hours = f"hasta las {clock(end)}"
    else:
        hours = ""
    label = " · ".join(part for part in (day_label, hours) if part)
    return label[:1].upper() + label[1:] if label else "Horario flexible"


def positive_availability(text):
    for label, window in TIME_OPTIONS.items():
        if text == normalize(label):
            return label, window
    if re.search(r"\b(?:cualquier (?:dia|horario|hora)|horario flexible|todo el dia|tengo flexibilidad)\b", text):
        return "Horario flexible", TIME_OPTIONS["Horario flexible"]
    days = tuple(i for i, day in enumerate(DAYS) if re.search(r"\b" + normalize(day) + r"s?\b", text))
    if not days:
        if re.search(r"\bfin(?:es)? de semana\b", text):
            days = (5, 6)
        elif "entre semana" in text:
            days = (0, 1, 2, 3, 4)
    time_pattern = HOUR
    start_pattern = r"\b(?:despues de|desde|a partir de|salgo a) (?:las )?" + time_pattern
    end_pattern = r"\b(?:hasta|antes de) (?:las )?" + time_pattern
    beginning, ending = re.search(start_pattern, text), re.search(end_pattern, text)
    interval = re.search(r"\b(?:de|entre) (?:las )?" + time_pattern + r"\s*(?:a|y|-)\s*(?:las )?" + time_pattern, text)
    exact = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    start, end = 0, 1440
    if interval:
        start = minutes(interval[1], interval[2] or 0)
        end = minutes(interval[3], interval[4] or 0)
    elif beginning or ending:
        if beginning:
            start = minutes(beginning[1], beginning[2] or 0)
        if ending:
            end = minutes(ending[1], ending[2] or 0)
    elif exact:
        start = minutes(exact[1], exact[2])
        end = start + 1
    elif re.search(r"\b(?:por|en) la manana\b", text):
        end = 720
    elif re.search(r"\b(?:por|en) la tarde\b", text):
        start = 720
    if start >= end or (not days and (start, end) == (0, 1440)):
        return None
    days = days or ALL_DAYS
    return availability_label(days, start, end), (days, start, end)


def read_availability(text):
    if not re.search(NEGATIVE_TIME, text):
        return positive_availability(text)
    clauses = re.split(r"[,;]|\b(?:pero|sino)\b|(?=\bsolo (?:los |el )?(?:lunes|martes|miercoles|jueves|viernes|sabados?|domingos?)\b)", text)
    positive = [part for part in clauses if not re.search(NEGATIVE_TIME, part)]
    parsed = positive_availability(" ".join(positive))
    if not parsed:
        return None
    _, (days, start, end) = parsed
    for part in clauses:
        if not re.search(NEGATIVE_TIME, part):
            continue
        blocked = positive_availability(re.sub(NEGATIVE_TIME, "", part).strip())
        if not blocked:
            continue
        _, (blocked_days, lower, upper) = blocked
        intersection = set(days).intersection(blocked_days)
        if not intersection or upper <= start or lower >= end:
            continue
        if lower == 0 and upper == 1440:
            days = tuple(day for day in days if day not in blocked_days)
        elif intersection != set(days) or (start < lower and upper < end):
            return None  # Hacen falta franjas distintas según el día.
        elif lower <= start:
            start = max(start, upper)
        else:
            end = min(end, lower)
    return (availability_label(days, start, end), (days, start, end)) if days and start < end else None


def ask_time_confirmation(text):
    """Return normalized text, or ask before using an uncertain time."""
    state = st.session_state.nexo
    work = re.search(r"(?<!no )\b(?:trabajo|estoy trabajando|tengo turno|mi turno es)\b", text)
    work_text = text[work.end():] if work else ""
    explicit = re.search(r"\b(?:(?:no )?puedo|(?:no )?estoy disponible|tengo libre|tengo tiempo|solo (?:los|el))\b", work_text)
    if explicit:
        return ask_time_confirmation(work_text[explicit.start():])
    work_range = re.search(r"\bde (?:las )?" + HOUR + r"\s*(?:a|-)\s*(?:las )?" + HOUR, work_text)
    work_end = re.search(r"\bhasta (?:las )?" + HOUR, work_text)
    if work_range or work_end:
        minute = minutes(work_range[3], work_range[4] or 0) if work_range else minutes(work_end[1], work_end[2] or 0)
        label = f"Después de las {clock(minute)}"
        state["time_choices"] = ((label, (ALL_DAYS, minute, 1440)),)
        reply(f"Entiendo que trabajas hasta las {clock(minute)}. ¿Puedes participar después de esa hora?",
              actions=[choice(label, "confirm_time", state["time_choices"][0]), choice("Indicar otro horario", "change_time")])
        return None

    match = re.search(HOUR_WORD, text)
    if not match:
        if work and re.search(r"\b(?:lunes|martes|miercoles|jueves|viernes|sabados?|domingos?|durante el dia|por la manana|por la tarde)\b", work_text):
            state["availability"] = state["time_label"] = None
            state["context"]["availability_confirmed"] = False
            ask("availability")
            return None
        return text
    hour = SPOKEN_HOURS[match[2]]
    if match[3]:
        shift = DAY_PART_SHIFT[match[3]]
        hour = hour % 12 + shift
        rewritten = text[:match.start()] + f"{match[1]} {hour}:00" + text[match.end():]
        return ask_time_confirmation(rewritten)
    if not re.search(r"\b(?:despues de|desde|a partir de|hasta|antes de|a las?)\b", text):
        return text
    candidates = (hour % 12, hour % 12 + 12)
    choices = []
    for candidate in candidates:
        rewritten = text[:match.start()] + f"{match[1]} {candidate}:00" + text[match.end():]
        work_clause = re.search(r"\btrabajo\b[^.!?;]*?\bhasta\b", rewritten)
        parsed = (f"Después de las {candidate:02d}:00", (ALL_DAYS, candidate * 60, 1440)) if work_clause else read_availability(rewritten)
        if parsed:
            choices.append(parsed)
    if not choices:
        return text
    state["time_choices"] = tuple(choices)
    reply(f"¿Con «{match[2]}» te refieres a las {clock(candidates[0] * 60)} o a las {clock(candidates[1] * 60)}?",
          actions=[choice(label, "confirm_time", (label, window)) for label, window in choices])
    return None


def set_availability(label, window):
    state = st.session_state.nexo
    state["availability"] = window
    state["time_label"] = label
    days, start, _ = window
    state["context"]["availability_confirmed"] = True
    state["context"]["after_18h_or_weekend"] = start >= 1080 or all(day >= 5 for day in days)


def read_location(text, waiting):
    district = None
    for code, name in DISTRICTS.items():
        name = normalize(name)
        if code == "DIST_HORIZON" and waiting == "institution_id" and text.strip(" .¡!?¿") == name:
            continue
        if code == "DIST_HORIZON" and waiting != "district_id" and text.strip(" .¡!?¿") != name:
            district_text = re.sub(r"\bestudio en (?:la )?horizonte\b", "", text)
            if not re.search(r"\b(?:distrito|en|me muevo por) (?:el distrito )?horizonte\b", district_text):
                continue
        if re.search(r"\b" + name + r"\b", text):
            district = code
            break
    institution = None
    if re.search(r"\bnova(?: aether)?\b", text):
        institution = "UNI_NOVA_AETHER"
    elif re.search(r"\bnexus\b", text):
        institution = "INST_NEXUS"
    elif re.search(r"\b(?:universidad |uni |estudio en (?:la )?)horizonte\b", text) or (waiting == "institution_id" and text.strip(" .") == "horizonte"):
        institution = "UNI_HORIZONTE"
    return district, institution


def read_schedule(raw):
    pattern = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:-(Mon|Tue|Wed|Thu|Fri|Sat|Sun))? (\d\d):(\d\d)-(\d\d):(\d\d)"
    match = re.fullmatch(pattern, str(raw).strip())
    if not match:
        return None
    first, last, sh, sm, eh, em = match.groups()
    begin = DATAPACK_DAYS.index(first)
    finish = DATAPACK_DAYS.index(last or first)
    opening, closing = minutes(sh, sm), minutes(eh, em)
    if begin > finish or not (0 <= opening < closing <= 1440) or int(sm) >= 60 or int(em) >= 60:
        return None
    day_label = DAYS[begin] if begin == finish else f"{DAYS[begin]} a {DAYS[finish]}"
    return (tuple(range(begin, finish + 1)), opening, closing,
            f"{day_label.capitalize()} · {sh}:{sm} a {eh}:{em}")


def is_compatible(service, availability):
    schedule = read_schedule(service.get("schedule"))
    if not schedule:
        return False
    days, start, end = availability
    open_days, opens, closes, _ = schedule
    return bool(set(days).intersection(open_days)) and opens < end and start < closes


def date_text(value):
    parsed = date.fromisoformat(str(value)[:10])
    return f"{parsed.day} {MONTHS[parsed.month - 1]} {parsed.year}"


def is_past(item):
    if item["kind"] != "event":
        return False
    return date.fromisoformat(str(item["end_date"])[:10]) < SCENARIO_DATE


def event_status(item):
    return "Fecha pasada" if is_past(item) else "En el calendario del escenario"


def event_day_overlap(item):
    available = st.session_state.nexo["availability"]
    if not available:
        return True
    start = date.fromisoformat(str(item["start_date"])[:10])
    end = date.fromisoformat(str(item["end_date"])[:10])
    return any((day - start.weekday()) % 7 <= (end - start).days for day in available[0])


def describe(kind, record, match_schedule=False, source_record=None):
    district = district_name(record["district_id"])
    if kind == "event":
        first, last = date_text(record["start_date"]), date_text(record["end_date"])
        return {
            "kind": kind, "title": record["title"], "type": "Actividad del calendario", "district": district,
            "when": first if first == last else f"{first} al {last}", "end_date": record["end_date"],
            "start_date": record["start_date"], "event_type": record["event_type"],
            "organizer": institution_name(record["institution_id"]), "reasons": record.get("reasons", []),
            "source": "D7 · Calendario académico de Ciudad Aethera.",
        }
    schedule = read_schedule(record.get("schedule"))
    raw_channels = record.get("channels") or ""
    channels = raw_channels.split(",") if isinstance(raw_channels, str) else raw_channels
    channel_labels = [CHANNELS.get(channel.strip(), channel.strip()) for channel in channels if channel.strip()]
    reasons = []
    if match_schedule:
        context = st.session_state.nexo["context"]
        reasons.append("Está en el distrito que indicaste." if record["district_id"] == context["district_id"] else f"Está en otro distrito, {district}.")
        reasons.append("El horario publicado coincide en parte con tu disponibilidad.")
        reasons.append("Es un espacio de apoyo entre estudiantes.")
    source = "D6 · Mapa de servicios de Ciudad Aethera."
    wait_days = record.get("average_wait_days")
    if isinstance(wait_days, Real) and isfinite(wait_days):
        source += f" D2 · {wait_days:g} días de espera en promedio en el histórico del servicio. La espera actual debe confirmarse."
    access = {}
    fields = {
        "Dirección": ("address", "street_address"),
        "Teléfono": ("phone_number", "contact_phone", "phone"),
        "Correo": ("email", "contact_email"),
        "Enlace": ("contact_url", "registration_url", "website"),
        "Indicaciones de acceso": ("access_instructions", "participation_instructions"),
    }
    for label, keys in fields.items():
        for key in keys:
            value = (source_record or {}).get(key)
            if isinstance(value, str) and value.strip():
                access[label] = value.strip()
                break
    return {
        "kind": kind, "title": record["name"],
        "type": "Apoyo entre pares" if record["service_type"] == "peer_support" else "Orientación institucional",
        "district": district, "when": schedule[3] if schedule else "Horario por confirmar",
        "channels": " y ".join(channel_labels) or "Canales por confirmar", "channel_codes": tuple(
            channel.strip() for channel in channels if channel.strip()),
        "access": access, "reasons": reasons, "source": source,
    }


def choice(label, action, value=None):
    return label, action, value


def ai_result(status):
    """Una caída de red, una respuesta inválida o un SDK ausente jamás bloquean el chat."""
    state = st.session_state.nexo
    if status == "used":
        state["ai_failures"] = 0
        state["ai_backoff_until"] = 0.0
    elif status not in ("no_key", "skipped"):
        state["ai_failures"] += 1
        if state["ai_failures"] >= 2 or status in ("quota", "credentials", "sdk_missing", "model_missing"):
            state["ai_backoff_until"] = time.monotonic() + AI_PAUSE_SECONDS


def begin_ai_turn(text, *, action=None, local_reason=None):
    state = st.session_state.nexo
    state["ai_style"] = None
    state["ai_output"] = "Redacción verificada de NEXO"
    state["interpretation"] = local_reason or ("Selección del usuario" if action else "Reglas de NEXO")
    if local_reason:
        return None
    key = setting("GEMINI_API_KEY")
    if not key:
        return None
    if time.monotonic() < state["ai_backoff_until"]:
        state["interpretation"] = "Gemini en pausa automática · respuesta por reglas"
        return None
    model = setting("NEXO_GEMINI_MODEL", DEFAULT_MODEL)
    pending = ("invitacion" if state["scope_pending"] else "horario" if state["time_choices"] else
               "interes" if state["interest_pending"] else None)
    try:
        plan, version, status = interpret_turn(
            text, key, model, selected_title=state["selected"]["title"] if state["selected"] else None,
            waiting=state["waiting"], context=state["context"], action=action, pending=pending,
        )
        if status == "used":
            plan = validate_turn(plan)
            if plan is None:
                status = "invalid_response"
    except Exception:
        plan, version, status = None, None, "unavailable"
    if status != "used" and status not in AI_FAILURE_REASONS:
        status = "unavailable"
    ai_result(status)
    if status != "used":
        state["interpretation"] = f"Gemini · {AI_FAILURE_REASONS[status]} · respuesta por reglas"
        return None
    state["ai_style"] = plan["style"]
    if action:
        state["interpretation"] = f"Gemini · {version or model} · estilo para la acción seleccionada"
    else:
        state["interpretation"] = f"Gemini · {version or model} · intención propuesta: {plan['intent']}"
    return plan


def reply(text, *, card=None, kind=None, options=(), actions=(), hint=None, step=None):
    state = st.session_state.nexo
    style = state["ai_style"]
    if style in ("cercano", "orientador") and state["context"]["goal"] != "human_support":
        index = 1 if style == "orientador" else 0
        for start, alternatives in RESPONSE_VARIANTS.items():
            if text.startswith(start):
                text = alternatives[index] + text[len(start):]
                state["ai_output"] = f"Variante {style} seleccionada por Gemini · datos verificados por NEXO"
                break
    st.session_state.nexo["messages"].append({
        "role": "assistant", "content": text, "card": card, "kind": kind, "options": options,
        "actions": actions, "hint": hint, "step": step,
    })


def ask(field):
    state = st.session_state.nexo
    state["waiting"] = field
    if field == "availability":
        reply("¿Cuándo puedes participar? Puedes decirme el día o el horario que te acomoda.",
              actions=[choice(label, "time", label) for label in TIME_OPTIONS])
    elif field == "district_id":
        text = "¿En qué distrito te mueves normalmente?"
        if state["context"]["goal"] == "human_support":
            text = ("Siento que estés pasando por esto. Puedo ayudarte a buscar un equipo de orientación "
                    "en el catálogo de Aethera. ¿En qué distrito buscas apoyo?")
        reply(text, actions=[choice(label, "district_id", code) for code, label in DISTRICTS.items()])
    else:
        reply("¿En qué institución estudias?",
              actions=[choice(label, "institution_id", code) for code, label in INSTITUTIONS.items()])


def alternative():
    state = st.session_state.nexo
    result = state["result"] or {}
    selected = state["selected"]
    group = "referrals" if state["context"]["goal"] == "human_support" else "peers"
    items = result.get(group, [])
    if selected not in items:
        return None
    index = items.index(selected) + 1
    return items[index] if index < len(items) else None


def item_actions(item):
    state = st.session_state.nexo
    result = state["result"] or {}
    actions = []
    if not is_past(item):
        label = {
            "peer": "Cómo participar", "event": "Qué conviene confirmar", "support": "Ver canales de atención",
        }[item["kind"]]
        actions.append(choice(label, "how"))
    if alternative() and item["kind"] != "event":
        label = "Ver otro recurso" if item["kind"] == "support" else "Ver otra opción"
        actions.append(choice(label, "other"))
    if result.get("events"):
        label = "Volver a actividades" if item["kind"] == "event" else "Ver actividades"
        actions.append(choice(label, "events"))
    if state["context"]["goal"] != "human_support":
        actions.append(choice("Cambiar horario", "change_time"))
    return actions


def show_item(item, text):
    st.session_state.nexo["selected"] = item
    reply(text, card=item, actions=item_actions(item))


def resolve():
    state = st.session_state.nexo
    context = state["context"]
    support = context.get("goal") == "human_support"
    signature = (context["goal"], context["district_id"], context["institution_id"], state["availability"])
    if state["result_key"] != signature:
        state["result"] = state["selected"] = None
        state["sources"] = ()
    state["waiting"] = None
    if not support and not state["availability"]:
        return ask("availability")
    if not context["district_id"]:
        return ask("district_id")
    if not support and not context["institution_id"]:
        return ask("institution_id")
    if not state["result"]:
        calendar, support_history, services = catalog()
        eligible = services
        unknown_schedules = False
        if not support:
            peer_rows = services["service_type"].eq("peer_support")
            unknown_schedules = any(read_schedule(raw) is None for raw in services.loc[peer_rows, "schedule"])
            compatible = services["schedule"].apply(lambda raw: is_compatible({"schedule": raw}, state["availability"]))
            eligible = services[~peer_rows | compatible]
        result = run_nexo(calendar, eligible, support_history, {**context, "schedule_filtered": not support})
        by_service = {record["service_id"]: record for record in services.to_dict("records")}
        state["sources"] = tuple(result.get("tools_used", ()))

        def service_card(kind, record):
            service_id = record.get("service_id") or record.get("id")
            return describe(kind, record, match_schedule=kind == "peer", source_record=by_service[service_id])

        if support:
            referrals = sorted(result["referrals"], key=lambda record: record["service_type"] != "counseling")
            state["result"] = {"referrals": [service_card("support", record) for record in referrals]}
        else:
            state["result"] = {
                "peers": [service_card("peer", record) for record in result["peer_services"]],
                "events": sorted([describe("event", record) for record in result["events"]], key=is_past),
                "unknown_schedules": unknown_schedules,
            }
        state["result_key"] = signature
    if support:
        items = state["result"]["referrals"]
        if items:
            return show_item(items[0], f"Siento que estés pasando por esto. En {items[0]['district']} figura "
                             "este recurso de apoyo humano en el catálogo de demostración de Aethera. "
                             "Puedes revisar sus canales y horario. La atención clínica corresponde a profesionales de salud.")
        return reply("No encontré un equipo de orientación registrado para ese distrito. Puedes consultar directamente "
                     "a bienestar estudiantil de tu institución o revisar otro distrito.",
                     actions=[choice("Buscar en otro distrito", "change_area")])
    peers = state["result"]["peers"]
    events = state["result"]["events"]
    if state["search_kind"] == "events":
        return show_events()
    if not peers:
        actions = [choice("Probar otro horario", "change_time"), choice("Buscar en otro distrito", "change_area")]
        if events:
            actions.append(choice("Ver actividades", "events"))
        district = district_name(context["district_id"])
        coverage = "Algunos servicios no tienen un horario que pueda verificar." if state["result"]["unknown_schedules"] else (
            "Tampoco encontré coincidencias en los horarios publicados para otros distritos del catálogo.")
        return reply(f"No encontré espacios de pares compatibles en {district} con {state['time_label'].lower()}. "
                     f"{coverage} Podemos probar otro horario o revisar las fechas de actividades.",
                     actions=actions)
    first = peers[0]
    if first["district"] == district_name(context["district_id"]):
        return show_item(first, f"Empezaría por este espacio en {first['district']}. Su horario coincide con tu disponibilidad.")
    district = district_name(context["district_id"])
    return reply(f"No encontré espacios de pares compatibles en {district} con ese horario. "
                 f"Encontré una opción en {first['district']}. ¿Qué prefieres?",
                 actions=[choice("Ver opción en " + first["district"], "peer"),
                          choice("Probar otro horario", "change_time"),
                          choice("Buscar en otro distrito", "change_area")])


def show_events():
    result = st.session_state.nexo["result"] or {}
    items = result.get("events", [])
    actions = [choice("Volver a espacios", "peer")] if result.get("peers") else [
        choice("Buscar en otro distrito", "change_area"), choice("Probar otro horario", "change_time")]
    if not items:
        return reply("El calendario no trae actividades para tu institución o distrito. Podemos ampliar la búsqueda.", actions=actions)
    interest_note = ""
    interest = st.session_state.nexo["interest"]
    if interest:
        pattern = INTERESTS.get(interest, r"\b" + re.escape(normalize(interest)) + r"\b")
        matches = [item for item in items if re.search(pattern, normalize(item["title"]))]
        if matches:
            items = matches
            interest_note = "Estas actividades mencionan tu interés en el título. "
        else:
            interest_note = f"No encontré una coincidencia documentada para {interest}. Puedes revisar las actividades generales. "
    items = sorted(items, key=lambda item: (is_past(item), not event_day_overlap(item)))
    day_note = (
        "Las fechas registradas para las actividades vigentes no coinciden con tus días indicados. "
        if any(not is_past(item) for item in items)
        and not any(not is_past(item) and event_day_overlap(item) for item in items)
        else ""
    )
    reply(interest_note + day_note + f"Estas actividades figuran en el calendario del escenario al {date_text(SCENARIO_DATE)}. "
          "El catálogo trae fechas. La hora exacta se confirma con la institución.",
          options=items, actions=actions)


def participation_step(item):
    name = item["title"]
    if item["kind"] == "event":
        return f"Consulta por {name} en {item['organizer']}." if item["organizer"] != "Interuniversitaria" else (
            f"Pregunta a tu institución quién coordina {name} en {item['district']}.")
    access = item["access"]
    if access.get("Indicaciones de acceso"):
        return access["Indicaciones de acceso"]
    if "Correo" in access:
        return f"Escribe al correo registrado para {name} y consulta si necesitas agendar."
    if "Teléfono" in access:
        return f"Llama al número registrado de {name} y pregunta si puedes asistir sin cita."
    if "Enlace" in access:
        return f"Revisa en el enlace registrado de {name} cómo se solicita una atención."
    if "Dirección" in access and "in_person" in item["channel_codes"]:
        return f"Consulta con la institución si puedes acudir a {name} en el horario publicado o si tienes que agendar."
    missing = "el punto de atención"
    if "phone" in item["channel_codes"]:
        missing += " o el teléfono oficial"
    elif "digital" in item["channel_codes"]:
        missing += " o el acceso digital"
    return f"Consulta a tu institución por {missing} de {name} y confirma si necesitas agendar antes de asistir."

def show_fact(field, item):
    if field == "location":
        address = item.get("access", {}).get("Dirección")
        if address:
            detail = f"La dirección registrada es {address}."
        elif item["kind"] == "event":
            detail = "El calendario D7 no incluye el recinto exacto. Puedes consultarlo con la institución que organiza la actividad."
        else:
            detail = "El catálogo D6 no incluye la dirección exacta. Puedes pedirle a la institución el punto de atención."
        text = f"{item['title']} figura en {item['district']}. {detail}"
    elif field in ("Teléfono", "Correo", "Enlace", "Inscripción", "Cupos"):
        value = item.get("access", {}).get(field)
        if value:
            text = f"{field} publicado para {item['title']}: {value}."
        else:
            missing = {
                "Teléfono": "el número oficial",
                "Correo": "el correo oficial",
                "Enlace": "un enlace de contacto",
                "Inscripción": "si necesitas inscribirte o agendar",
                "Cupos": "si hay cupos disponibles",
            }[field]
            text = (f"El catálogo no confirma {missing} para {item['title']}. "
                    f"{participation_step(item)}")
    elif item["kind"] == "event":
        text = f"{item['title']} figura para {item['when']}. El calendario no registra una hora exacta."
        if is_past(item):
            text += " La fecha ya pasó dentro del escenario de la demo."
    else:
        text = f"El horario publicado de {item['title']} es {item['when']}."
    reply(text, actions=item_actions(item))


def named_item(text):
    state = st.session_state.nexo
    result = state["result"] or {}
    items = ([state["selected"]] if state["selected"] else []) + [
        item for group in ("peers", "events", "referrals") for item in result.get(group, [])]
    for item in items:
        if re.search(r"\b" + re.escape(normalize(item["title"])) + r"\b", text):
            return item
    if not re.search(r"\bespacio (?!de\b|que\b|recomendado\b|anterior\b)\w+|\b\w+ (?:pares|orientacion|trayectoria)\b", text):
        return None
    _, _, services = catalog()
    for service in services.to_dict("records"):
        name = normalize(service["name"]).removeprefix("espacio ")
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            state["sources"] = ("D6 · Servicios",)
            kind = "peer" if service["service_type"] == "peer_support" else "support"
            return describe(kind, service, source_record=service)
    return None


def access_note(item):
    access = item["access"]
    missing = []
    if "in_person" in item["channel_codes"] and "Dirección" not in access:
        missing.append("la dirección exacta")
    if "phone" in item["channel_codes"] and "Teléfono" not in access:
        missing.append("el teléfono oficial")
    if "digital" in item["channel_codes"] and not {"Correo", "Enlace"}.intersection(access):
        missing.append("el enlace o correo de atención")
    if missing:
        return "El catálogo no especifica " + " ni ".join(missing) + "."
    return "La necesidad de agendar y los cupos se confirman con la institución."


def show_next_step():
    state = st.session_state.nexo
    item = state["selected"]
    if not item:
        return reply("Para orientarte sobre cómo participar, primero busquemos una opción.", actions=[choice("Retomar búsqueda", "resume")])
    if is_past(item):
        return reply("Esa fecha ya pasó en el calendario de la demo. Puedes revisar otra actividad.",
                     actions=[choice("Ver actividades", "events")])
    if item["kind"] == "event":
        hint = "El calendario no especifica la hora exacta, el recinto ni el proceso de inscripción."
        intro = "Puedes confirmar los detalles con quien organiza la actividad."
    else:
        hint = access_note(item)
        intro = "Estos son los datos de atención que figuran en el catálogo."
    reply(intro, card=item, kind="next", hint=hint, step=participation_step(item),
          actions=[choice("Guardar próximo paso", "save"), *item_actions(item)[1:]])


def save_step():
    state = st.session_state.nexo
    item = state["selected"]
    if not item or is_past(item):
        return show_next_step()
    hint = participation_step(item)
    actions = [choice("Buscar integración", "start")] if state["context"]["goal"] == "human_support" else [
        choice("Ver actividades", "events"), choice("Cambiar horario", "change_time")]
    plan = {"title": item["title"], "step": hint}
    if state["saved"] == plan:
        return reply("Ese próximo paso ya está guardado durante esta sesión. Puedes verlo en el panel lateral.", actions=actions)
    state["saved"] = plan
    reply("Guardé tu próximo paso durante esta sesión. Puedes verlo en el panel lateral.", card=item, kind="saved", hint=hint, actions=actions)


def perform(action, value):
    state = st.session_state.nexo
    context = state["context"]
    if action == "retry_text":
        return handle_text(value)
    if action == "retry_action":
        return perform(*value)
    state["scope_pending"] = False
    state["time_choices"] = ()
    state["interest_pending"] = False
    if action in ("district_id", "institution_id"):
        context[action] = value
    elif action == "time":
        set_availability(value, TIME_OPTIONS[value])
    elif action == "confirm_time":
        set_availability(*value)
    elif action == "start":
        context["goal"] = "social_connection"
        state["search_kind"] = "peers"
    elif action == "start_events":
        context["goal"] = "social_connection"
        state["search_kind"] = "events"
    elif action == "change_time":
        context["goal"] = "social_connection"
        context["availability_confirmed"] = context["after_18h_or_weekend"] = False
        state["availability"] = state["time_label"] = None
    elif action == "change_area":
        context["district_id"] = None
    elif action == "events":
        return show_events()
    elif action == "event":
        return show_item(value, "Aquí está la información registrada en el calendario de Aethera.")
    elif action == "peer":
        state["search_kind"] = "peers"
        return show_item(state["result"]["peers"][0], "Podemos retomar este espacio.")
    elif action == "other":
        item = alternative()
        if item:
            label = "También puedes explorar este recurso de apoyo." if item["kind"] == "support" else f"También encontré esta opción en {item['district']}."
            return show_item(item, label)
        actions = [choice("Buscar en otro distrito", "change_area")]
        if (state["result"] or {}).get("events"):
            actions.insert(0, choice("Ver actividades", "events"))
        reply("Ya revisamos las opciones de esta búsqueda. Puedes ajustar el distrito o mirar el calendario si está disponible.",
              actions=actions)
        return
    elif action == "how":
        return show_next_step()
    elif action == "save":
        return save_step()
    context["goal"] = context["goal"] or "social_connection"
    resolve()


def scope_reply(academic=False):
    state = st.session_state.nexo
    state["scope_pending"] = True
    limit = "No puedo resolver ejercicios académicos." if academic else "Esa consulta está fuera del ámbito de NEXO."
    reply(f"{limit} Puedo ayudarte a encontrar actividades y espacios para conectar con otros estudiantes "
          "en Aethera. ¿Quieres buscar actividades que se ajusten a tu disponibilidad?",
          actions=[choice("Buscar actividades", "start_events"), choice("Conocer personas", "start")])


def urgent_support():
    state = st.session_state.nexo
    state["scope_pending"] = False
    state["time_choices"] = ()
    state["waiting"] = state["result"] = state["selected"] = None
    state["sources"] = ()
    state["context"]["goal"] = "human_support"
    # Orientación de la OMS ante peligro inmediato. Aethera es ficticia.
    # https://cdn.who.int/media/docs/default-source/campaigns-and-initiatives/world-mental-health-day/2021/suicide-living-es.pdf
    reply("Siento que estés pasando por esto. Si hay peligro inmediato o ya te hiciste daño, "
          "llama ahora a los servicios de emergencia de donde estés. Si puedes hacerlo con seguridad, avisa a una "
          "persona de confianza que pueda acompañarte. Los contactos de Aethera son simulados.")


def clarify():
    state = st.session_state.nexo
    if state["waiting"]:
        return ask(state["waiting"])
    if state["selected"]:
        item = state["selected"]
        reply(f"¿Quieres saber algo sobre {item['title']} o prefieres buscar otra opción?",
              actions=item_actions(item))
    else:
        reply("¿Buscas una actividad, un espacio para conocer gente o un recurso de apoyo universitario?",
              actions=[choice("Buscar actividades", "start_events"), choice("Conocer personas", "start")])


def explain(item):
    reasons = item["reasons"] or ["Este recurso figura en el catálogo de tu distrito."]
    reply(f"Estos son los criterios que usé para mostrar {item['title']}:", options=reasons,
          kind="reasons", hint=item["source"], actions=item_actions(item))


def confirmation(accepted, scope_pending, time_choices, interest_pending):
    state = st.session_state.nexo
    if scope_pending:
        if accepted:
            return perform("start_events", None)
        state["scope_pending"] = False
        return reply("De acuerdo. Si quieres retomar la búsqueda más adelante, puedes escribirme.")
    if time_choices:
        if not accepted:
            return perform("change_time", None)
        if len(time_choices) == 1:
            return perform("confirm_time", time_choices[0])
        state["time_choices"] = time_choices
        return reply("¿Cuál de estos horarios quisiste indicar?",
                     actions=[choice(label, "confirm_time", (label, window)) for label, window in time_choices])
    if not accepted:
        state["interest_pending"] = False
    if accepted and interest_pending:
        return reply("¿Qué tema te interesa? Así puedo revisar los títulos del calendario.")
    return clarify()


def semantic_applied(intent):
    state = st.session_state.nexo
    state["interpretation"] = state["interpretation"].replace("intención propuesta: " + intent, "intención utilizada: " + intent)


def greeting():
    return reply("¡Hola! Soy NEXO. ¿Buscas actividades, un espacio para conocer gente u orientación universitaria?",
                 actions=[choice("Buscar integración", "start")])


def thanks():
    state = st.session_state.nexo
    return reply("De nada. Tu próximo paso está en el panel lateral." if state["saved"]
                 else "De nada. Podemos seguir explorando cuando quieras.")


def followup_item(text):
    item = named_item(text)
    if item:
        return item
    named = re.search(r"\bespacio (?!de\b|que\b|recomendado\b|anterior\b|actual\b|tiene\b|esta\b|es\b|queda\b)\w+", text)
    return None if named else st.session_state.nexo["selected"]


def ask_followup_item():
    return reply("¿De qué espacio o actividad quieres saber? Escribe el nombre que aparece en el catálogo.",
                 actions=[choice("Buscar actividades", "start_events"), choice("Conocer personas", "start")])


def handle_text(text, use_model=True, demo=False):
    state = st.session_state.nexo
    context = state["context"]
    t = normalize(text)
    clean = t.strip(" .!¡?¿")
    context.pop("llm_interpreted_need", None)
    danger = re.search(
        r"\b(?:me (?:quiero|voy a) (?:matar|suicidar|morir|hacer dano|lastimar|quitar la vida)|"
        r"(?:quiero|voy a|pienso|estoy pensando en|tengo ganas de|estoy a punto de) "
        r"(?:suicidarme|matarme|morir|morirme|hacerme dano|lastimarme|quitarme la vida)|"
        r"tengo (?:pensamientos suicidas|un plan para suicidarme)|"
        r"(?:ya )?me (?:hice dano|lastime a proposito)|me acabo de hacer dano|tome demasiadas pastillas|"
        r"(?:estoy en|hay|corro) (?:un )?(?:peligro|riesgo) inmediato|"
        r"me estan (?:atacando|amenazando) ahora|(?:se|lo|la) (?:va a|quiere) (?:matar|suicidar|hacer dano))\b", clean)
    if danger:
        begin_ai_turn(text, local_reason="Protocolo local de seguridad")
        return urgent_support()

    support = bool(SUPPORT_PATTERN.search(clean)) or clean == "necesito ayuda"
    local_reason = None
    if not demo and (support or context["goal"] == "human_support"):
        local_reason = "Orientación local de apoyo humano"
    elif not use_model:
        local_reason = "Reglas de NEXO"
    ai = begin_ai_turn(text, action="demo" if demo else None, local_reason=local_reason)
    semantic = ai["intent"] if ai else None
    scope_pending = state["scope_pending"]
    time_choices = state["time_choices"]
    interest_pending = state["interest_pending"]

    if clean in ("si", "si por favor", "si, por favor", "ya", "dale", "claro"):
        return confirmation(True, scope_pending, time_choices, interest_pending)
    if clean in ("no", "no gracias", "no, gracias"):
        return confirmation(False, scope_pending, time_choices, interest_pending)
    if time_choices:
        exact = re.fullmatch(r"(?:a las |las )?([01]?\d|2[0-3])(?::([0-5]\d))?(?: horas?)?", clean)
        if exact:
            minute = minutes(exact[1], exact[2] or 0)
            for label, window in time_choices:
                if clock(minute) in label:
                    return perform("confirm_time", (label, window))
    state["scope_pending"] = False
    state["time_choices"] = ()
    if re.fullmatch(r"hola(?: nexo)?|holi|buen[oa]s? (?:dias|tardes|noches)|buenas|que tal", clean):
        return greeting()
    if clean in ("gracias", "muchas gracias"):
        return thanks()
    social = re.search(r"\b(conocer (?:a )?gente|conocer personas|hacer amig\w*|integrarme|integracion|actividades|eventos|vida universitaria|apoyo entre pares)\b", clean)
    wants_events = re.search(r"\b(?:buscar|encontrar|ver|mirar|revisar|explorar) (?:las |los |alguna |algun )?(?:actividades?|eventos?|calendario)\b", clean)
    wants_peers = re.search(r"\b(?:conocer (?:a )?(?:mas )?(?:gente|personas|companer\w*)|hacer amig\w*|apoyo entre pares|buscar (?:un )?espacio)\b", clean)
    academic = not wants_events and re.search(
        r"\b(?:derivadas?|ecuaciones?|integrales?|ejercicios? (?:academicos?|de (?:calculo|matematicas|fisica))|"
        r"(?:hacer|resolver|explicar) (?:mi |la |una )?tarea)\b", clean)
    outside_topic = re.search(r"\b(receta|chiste|bitcoin|horoscopo|capital de|pronostico del tiempo|programar en python)\b", clean)
    if not support and (academic or outside_topic):
        return scope_reply(academic=bool(academic))
    district, institution = read_location(t, state["waiting"])
    item = state["selected"]
    if not support and re.search(r"\b(?:mis intereses|mis gustos|(?:que|algo) me guste)\b", clean):
        state["interest_pending"] = True
        return reply("¿Qué te interesa? Puedo buscar ese tema en los títulos del calendario de Aethera.")
    interest = next((label for label, pattern in INTERESTS.items() if re.search(pattern, clean)), None)
    semantic_interest = not interest and ai and ai["interest"] != "none" and semantic in ("activities", "interest")
    if semantic_interest and not support and not wants_peers:
        interest = ai["interest"]
    if not support and state["interest_pending"] and not interest and not (district or institution):
        short_interest = re.sub(r"^(?:me (?:gustan?|interesan?)|quiero buscar) (?:el |la |los |las )?", "", clean)
        if re.fullmatch(r"[\w]+(?: +[\w]+){0,3}", short_interest):
            interest = short_interest
    if not support and interest and (state["interest_pending"] or wants_events or semantic in ("interest", "activities") or re.search(
        r"\b(?:club|taller|actividad\w*|me gusta\w*|me interesa\w*|practicar|jugar)\b", clean)):
        if semantic_interest:
            semantic_applied(semantic)
        state["interest_pending"] = False
        state["interest"] = interest
        wants_events = True
    location_query = re.search(
        r"\b(?:donde (?:queda|esta|es|atienden|se (?:hace|realiza))|"
        r"(?:cual es|tienes|dame|sabes) (?:la|su) direccion|en que (?:parte|lugar|sede)|como (?:llego|llegar))\b", t)
    schedule_query = re.search(
        r"\b(?:a que hora|cual es (?:el|su) horario|en que horario|que horario tiene|"
        r"cuando (?:es|abre|abren|funciona|atiende|atienden|se (?:hace|realiza)))\b", t)
    contact_fields = {
        "Teléfono": r"\b(?:telefono|numero de contacto|numero oficial|llamar(?:les|los|las)?|como (?:les|los) llamo)\b",
        "Correo": r"\b(?:correo|e-?mail)\b",
        "Enlace": r"\b(?:link|enlace|pagina web)\b",
        "Cupos": r"\b(?:cupos?|quedan plazas)\b",
        "Inscripción": r"\b(?:necesito (?:una )?cita|hay que agendar|hay que inscribirse|requiere (?:cita|inscripcion)|piden inscripcion)\b",
    }
    contact_query = next((label for label, pattern in contact_fields.items() if re.search(pattern, t)), None)
    if not support and (location_query or schedule_query or contact_query):
        target = followup_item(t)
        if not target:
            return ask_followup_item()
        state["selected"] = target
        return show_fact("location" if location_query else ("schedule" if schedule_query else contact_query), target)
    if item and not support:
        if re.search(r"\b(?:como (?:participo|participar|puedo participar|me inscribo|contacto|agendo|doy el proximo paso)|que debo confirmar|por donde empiezo)\b", t):
            return show_next_step()
        if re.search(r"\b(?:por que|por cual razon|que te llevo a elegir)\b", t):
            return explain(item)
        if re.search(r"\b(?:otra (?:opcion|alternativa)|otro recurso|mas opciones|algo mas)\b", t):
            return perform("other", None)
        if re.search(r"\bguard(?:a|ar|ame)\b", t):
            return save_step()
    if district:
        context["district_id"] = district
    if institution:
        context["institution_id"] = institution
    if support:
        context["goal"] = "human_support"
        return resolve()
    if wants_events or wants_peers:
        context["goal"] = "social_connection"
        state["search_kind"] = "events" if wants_events else "peers"
    time_text = ask_time_confirmation(t)
    if time_text is None:
        context["goal"] = "social_connection"
        return
    available = read_availability(time_text)
    if re.search(r"\b(?:cambiar|ajustar) (?:mi |el )?(?:horario|disponibilidad)\b", t) and not available:
        return perform("change_time", None)
    if re.search(r"\b(?:otro distrito|cambiar (?:de )?distrito)\b", t) and not district:
        return perform("change_area", None)
    if (state["result"] or {}).get("events") and re.search(r"\b(?:actividades|eventos|calendario)\b", t) and not (district or institution or available):
        return show_events()
    if available:
        set_availability(*available)
    elif re.search(NEGATIVE_TIME, time_text):
        state["availability"] = state["time_label"] = None
        context["availability_confirmed"] = context["after_18h_or_weekend"] = False
        return ask("availability")
    if social:
        context["goal"] = "social_connection"
    if social or wants_events or wants_peers or available:
        context["goal"] = context["goal"] or "social_connection"
        return resolve()
    if (district or institution) and state["waiting"] and semantic != "human_support":
        context["goal"] = context["goal"] or "social_connection"
        return resolve()
    if semantic in ("yes", "no") and (scope_pending or time_choices or interest_pending):
        semantic_applied(semantic)
        return confirmation(semantic == "yes", scope_pending, time_choices, interest_pending)
    route = {
        "activities": ("start_events", None), "social_connection": ("start", None),
        "change_time": ("change_time", None), "change_area": ("change_area", None),
    }
    if semantic in route and not (semantic == "change_area" and district):
        semantic_applied(semantic)
        return perform(*route[semantic])
    if semantic == "human_support":
        semantic_applied(semantic)
        context["goal"] = "human_support"
        return resolve()
    if semantic == "out_of_context" and not (district or institution):
        semantic_applied(semantic)
        return scope_reply()
    if semantic == "interest":
        semantic_applied(semantic)
        state["interest_pending"] = True
        return reply("¿Qué tema te interesa? Puedo buscarlo en los títulos del calendario de Aethera.")
    if semantic in ("location", "schedule", "contact", "why", "how"):
        target = followup_item(t)
        semantic_applied(semantic)
        if not target:
            return ask_followup_item()
        state["selected"] = target
        if semantic in ("location", "schedule"):
            return show_fact(semantic, target)
        if semantic == "contact":
            focus = {"phone": "Teléfono", "email": "Correo", "link": "Enlace",
                     "capacity": "Cupos", "registration": "Inscripción"}.get(ai["focus"])
            return show_fact(focus, target) if focus else show_next_step()
        if semantic == "why":
            return explain(target)
        return show_next_step()
    if item and semantic in ("other", "save"):
        semantic_applied(semantic)
        return perform(semantic, None)
    if district or institution:
        context["goal"] = context["goal"] or "social_connection"
        return resolve()
    if semantic in ("greeting", "thanks", "availability"):
        semantic_applied(semantic)
        if semantic == "availability":
            return ask("availability")
        return greeting() if semantic == "greeting" else thanks()
    return clarify()


def record_user(text):
    st.session_state.nexo["messages"].append({"role": "user", "content": text})


def submit():
    text = (st.session_state.get("nexo_input") or "").strip()
    if text:
        record_user(text)
        safe_turn(handle_text, (text,), "retry_text", text)


def start_demo(label):
    new_conversation()
    text = DEMO_MESSAGES[label]
    record_user(text)
    safe_turn(handle_text, (text, True, True), "retry_text", text)


ACTION_MESSAGES = {
    "how": "¿Cómo doy el próximo paso?",
    "save": "Quiero guardar este próximo paso.",
    "events": "Quiero ver las actividades del calendario.",
    "change_time": "Quiero cambiar mi disponibilidad.",
    "change_area": "Quiero buscar en otro distrito.",
}


def click_action(label, action, value):
    text = ACTION_MESSAGES.get(action, label)
    record_user(text)
    safe_turn(handle_action, (text, action, value), "retry_action", (text, action, value))


def handle_action(text, action, value):
    if action == "retry_text":
        return handle_text(value)
    if action == "retry_action":
        return handle_action(*value)
    state = st.session_state.nexo
    local_reason = "Orientación local de apoyo humano" if state["context"]["goal"] == "human_support" else None
    begin_ai_turn(text, action=action, local_reason=local_reason)
    return perform(action, value)


def safe_turn(handler, args, retry_action, retry_value):
    state = st.session_state.nexo
    previous = {**state, "context": state["context"].copy(), "messages": state["messages"].copy()}
    try:
        handler(*args)
    except Exception as exc:
        LOG.warning("NEXO no completó un turno (%s)", type(exc).__name__)
        previous["ai_failures"] = state["ai_failures"]
        previous["ai_backoff_until"] = state["ai_backoff_until"]
        st.session_state.nexo = previous
        state = st.session_state.nexo
        state["ai_style"] = None
        state["ai_output"] = "Redacción verificada de NEXO"
        state["interpretation"] = "Error recuperable · búsqueda sin completar"
        reply("Ocurrió un problema al atender esa solicitud. Conservé los datos de tu búsqueda. Puedes intentarlo de nuevo.",
              actions=[choice("Volver a intentar", retry_action, retry_value)])


def render_card(item, kind=None, hint=None, step=None):
    if kind == "saved":
        title, tag, facts = item["title"], "Próximo paso guardado", ()
    elif item["kind"] == "event":
        title, tag = item["title"], "Para dar el próximo paso" if kind == "next" else item["type"]
        facts = (("Fecha registrada", item["when"]), ("Distrito", item["district"]), ("Organiza", item["organizer"]))
        if is_past(item):
            hint = "Fecha pasada dentro del escenario de simulación."
    elif kind == "next":
        title, tag = item["title"], "Cómo participar" if item["kind"] == "peer" else "Cómo contactar"
        district = item["district"]
        where = f"Distrito {district}" if district in DISTRICTS.values() else district
        facts = (("Dónde", where), ("Cuándo", item["when"]),
                 ("Canales", item["channels"]), *item["access"].items())
    else:
        title, tag = item["title"], item["type"]
        facts = (("Distrito", item["district"]), ("Horario", item["when"]))
    fact_html = "".join(f"<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>" for label, value in facts)
    if fact_html:
        fact_html = f'<dl class="nexo-facts">{fact_html}</dl>'
    hint_html = f'<p class="nexo-note">{escape(hint)}</p>' if hint else ""
    step_html = f'<p class="nexo-note"><strong>Tu próximo paso</strong><br>{escape(step)}</p>' if step else ""
    details_html = ""
    if item["reasons"] and kind is None:
        reasons = "".join(f"<li>{escape(reason)}</li>" for reason in item["reasons"])
        details_html = (
            '<details class="nexo-card-details"><summary>Por qué aparece esta opción</summary>'
            f'<ul>{reasons}</ul><p class="nexo-note">{escape(item["source"])}</p></details>'
        )
    st.markdown(
        f'<article class="nexo-card"><p class="nexo-type">{escape(tag)}</p>'
        f"<h3>{escape(title)}</h3>{fact_html}{step_html}{hint_html}{details_html}</article>",
        unsafe_allow_html=True,
    )


def render_attachment(message, index, active):
    card, kind = message["card"], message["kind"]
    if card:
        render_card(card, kind, message["hint"], message.get("step"))
    elif kind == "reasons":
        for reason in message["options"]:
            st.write("• " + reason)
        st.caption(message["hint"])
    elif message["options"]:
        for number, item in enumerate(message["options"]):
            st.markdown(
                f'<article class="nexo-event"><strong>{escape(item["title"])}</strong>'
                f'<p>{escape(item["when"])} · {escape(item["district"])} · {escape(event_status(item))}</p></article>',
                unsafe_allow_html=True,
            )
            if active:
                st.button("Ver detalles", key=f"nexo_event_{index}_{number}",
                          on_click=click_action, args=(f"Quiero ver {item['title']}.", "event", item))


def render_message(message, index, active):
    role = message["role"]
    with st.chat_message(role):
        if role == "user":
            st.text(message["content"])
            return
        st.write(message["content"])
        if message["card"] or message["options"]:
            if active:
                render_attachment(message, index, True)
            else:
                label = f"Ver {message['card']['title']}" if message["card"] else (
                    "Ver motivos de la recomendación" if message["kind"] == "reasons" else "Ver actividades de esta búsqueda")
                with st.expander(label):
                    render_attachment(message, index, False)
        if active and message["actions"]:
            with st.container(horizontal=True, gap="small"):
                for number, (label, action, value) in enumerate(message["actions"]):
                    button_type = "primary" if number == 0 and action in ("how", "save") else "secondary"
                    st.button(label, key=f"nexo_action_{index}_{number}", type=button_type,
                              on_click=click_action, args=(label, action, value))


if "nexo" not in st.session_state:
    new_conversation()
state = st.session_state.nexo

with st.sidebar:
    st.markdown("### Trazabilidad del Agente")
    st.caption(f"Distrito · {district_name(state['context']['district_id'])}")
    st.caption(f"Institución · {institution_name(state['context']['institution_id'])}")
    st.caption(f"Disponibilidad · {state['time_label'] or 'Por confirmar'}")
    with st.expander("Detalles técnicos"):
        st.write(f"Última interacción · {state['interpretation']}")
        st.caption(f"Respuesta · {state.get('ai_output', 'Redacción verificada de NEXO')}")
        st.caption("Fuentes de la búsqueda · " + (", ".join(state["sources"]) or "Sin consulta al catálogo"))
        st.json(state["context"])
    st.markdown("---")
    st.caption("Gemini en la conversación · respaldo local automático" if setting("GEMINI_API_KEY") else "Interpretación mediante reglas · sin API")
    if state["saved"]:
        st.markdown("**Próximo paso**")
        st.write(state["saved"]["title"])
        st.caption(state["saved"]["step"])
    st.button("Reiniciar conversación", on_click=new_conversation, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
for column, label in zip(st.columns(3), DEMO_MESSAGES):
    column.button(label, use_container_width=True, on_click=start_demo, args=(label,))

st.markdown("<br><br>", unsafe_allow_html=True)
for index, message in enumerate(state["messages"]):
    render_message(message, index, index == len(state["messages"]) - 1)

st.chat_input("Escribe tu consulta aquí...", key="nexo_input", on_submit=submit)
st.caption("Ciudad Aethera · Datos sintéticos de demostración")
