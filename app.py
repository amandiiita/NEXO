import streamlit as st
from data_loader import load_all_data
from agent import extract_context_from_text, run_nexo

st.set_page_config(page_title="NEXO", page_icon="🔗", layout="wide")

# Diccionarios para traducir códigos crudos del Data Pack a lenguaje humano
DISTRICT_LABELS = {
    "DIST_GAIA": "Distrito Gaia",
    "DIST_NEBULA": "Distrito Nébula",
    "DIST_VECTOR": "Distrito Vector",
    "DIST_HORIZON": "Distrito Horizonte",
    "DIST_QUANTUM": "Distrito Quantum",
    "ALL": "Toda Ciudad Aethera"
}

INSTITUTION_LABELS = {
    "UNI_NOVA_AETHER": "Universidad Nova Aether",
    "INST_NEXUS": "Instituto Nexus",
    "UNI_HORIZONTE": "Universidad Horizonte",
    "ALL": "Todas las instituciones"
}

SERVICE_TYPE_LABELS = {
    "peer_support": "Comunidad y Apoyo entre Pares",
    "counseling": "Orientación Profesional",
    "career_guidance": "Orientación de Trayectoria"
}

EVENT_TYPE_LABELS = {
    "university_activity": "Encuentro Estudiantil Universitario",
    "wellbeing_activity": "Semana de Pausa y Bienestar"
}


def format_schedule(raw_schedule):
    s = str(raw_schedule)
    s = s.replace("Mon-Sat", "Lunes a sábado ·").replace("Mon-Fri", "Lunes a viernes ·")
    return f"{s} hrs"


def format_channels(raw_channels):
    c = str(raw_channels)
    c = c.replace("in_person", "Presencial").replace("phone", "Teléfono").replace("digital", "Online / Digital")
    return c


def format_date_range(start_str, end_str):
    meses = {
        "01": "ene", "02": "feb", "03": "mar", "04": "abr",
        "05": "may", "06": "jun", "07": "jul", "08": "ago",
        "09": "sep", "10": "oct", "11": "nov", "12": "dic"
    }
    try:
        y1, m1, d1 = start_str.split("-")
        y2, m2, d2 = end_str.split("-")
        if start_str == end_str:
            return f"{int(d1)} de {meses.get(m1, m1)} de {y1}"
        return f"{int(d1)} de {meses.get(m1, m1)} al {int(d2)} de {meses.get(m2, m2)} de {y2}"
    except Exception:
        return f"{start_str} al {end_str}"


calendar, support_history, services = load_all_data()

if "student_context" not in st.session_state:
    st.session_state.student_context = {
        "goal": None,
        "district_id": None,
        "institution_id": None,
        "after_18h_or_weekend": False,
        "availability_confirmed": False
    }
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Barra lateral: Trazabilidad técnica para el jurado
with st.sidebar:
    st.markdown("### 🧠 Trazabilidad del Agente")
    st.caption("Estado interno estructurado por NEXO a partir de la conversación:")
    st.json(st.session_state.student_context)

    st.markdown("---")
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    st.success("🤖 Agente IA Generativa (Gemini) Activo")

    if st.button("🔄 Reiniciar conversación", use_container_width=True):
        st.session_state.student_context = {
            "goal": None, "district_id": None, "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False
        }
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()

# Encabezado principal
st.title("🔗 NEXO")
st.subheader("Encuentra dónde conectar en tu vida universitaria.")
st.write(
    "Cuéntanos tu disponibilidad y ubicación. NEXO cruza el calendario y los espacios de Ciudad Aethera "
    "para recomendarte oportunidades reales que se adaptan a tu rutina."
)

# Botones de demostración rápida para el video
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("💬 Demo Paso a Paso (Conversacional)", use_container_width=True):
        st.session_state.student_context = {
            "goal": None, "district_id": None, "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False
        }
        st.session_state.messages = []
        msg = "Quiero conocer gente en la universidad, pero trabajo 25 horas a la semana y salgo después de las 18:00."
        st.session_state.messages.append({"role": "user", "content": msg})
        st.session_state.student_context = extract_context_from_text(msg, st.session_state.student_context, api_key)
        res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
        st.session_state.last_result = res
        st.session_state.messages.append({"role": "assistant", "content": res["agent_message"]})
        st.rerun()

with c2:
    if st.button("⚡ Demo Caso 1 Directo (Integración)", use_container_width=True):
        st.session_state.student_context = {
            "goal": None, "district_id": None, "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False
        }
        st.session_state.messages = []
        msg = "Estudio en Nova Aether, me muevo por el distrito Nebula, trabajo 25 horas y quiero conocer gente después de las 18:00."
        st.session_state.messages.append({"role": "user", "content": msg})
        st.session_state.student_context = extract_context_from_text(msg, st.session_state.student_context, api_key)
        res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
        st.session_state.last_result = res
        st.session_state.messages.append({"role": "assistant", "content": res["agent_message"]})
        st.rerun()

with c3:
    if st.button("🚨 Demo Caso 2 (Derivación Humana Ética)", use_container_width=True):
        st.session_state.student_context = {
            "goal": None, "district_id": "DIST_NEBULA", "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False
        }
        st.session_state.messages = []
        msg = "Últimamente me siento muy mal emocionalmente y necesito hablar con alguien en Nebula."
        st.session_state.messages.append({"role": "user", "content": msg})
        st.session_state.student_context = extract_context_from_text(msg, st.session_state.student_context, api_key)
        res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
        st.session_state.last_result = res
        st.session_state.messages.append({"role": "assistant", "content": res["agent_message"]})
        st.rerun()

st.markdown("---")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# Botones rápidos cuando NEXO pregunta un dato faltante
res = st.session_state.last_result
if res and res["status"] == "needs_info":
    missing = res.get("missing_field")
    if missing == "district_id":
        st.caption("Selecciona tu distrito o escríbelo abajo:")
        d_cols = st.columns(5)
        for idx, (label, code) in enumerate([
            ("Distrito Nébula", "DIST_NEBULA"), ("Distrito Gaia", "DIST_GAIA"),
            ("Distrito Vector", "DIST_VECTOR"), ("Distrito Horizonte", "DIST_HORIZON"),
            ("Distrito Quantum", "DIST_QUANTUM")
        ]):
            if d_cols[idx].button(f"📍 {label}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": label})
                st.session_state.student_context["district_id"] = code
                new_res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
                st.session_state.last_result = new_res
                st.session_state.messages.append({"role": "assistant", "content": new_res["agent_message"]})
                st.rerun()

    elif missing == "institution_id":
        st.caption("Selecciona tu institución o escríbela abajo:")
        i_cols = st.columns(3)
        for idx, (label, code) in enumerate([
            ("Universidad Nova Aether", "UNI_NOVA_AETHER"),
            ("Instituto Nexus", "INST_NEXUS"),
            ("Universidad Horizonte", "UNI_HORIZONTE")
        ]):
            if i_cols[idx].button(f"🏫 {label}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": label})
                st.session_state.student_context["institution_id"] = code
                new_res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
                st.session_state.last_result = new_res
                st.session_state.messages.append({"role": "assistant", "content": new_res["agent_message"]})
                st.rerun()

# Input conversacional
user_input = st.chat_input("Escribe aquí lo que buscas (ej: 'Quiero conocer gente pero salgo tarde de trabajar')...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.student_context = extract_context_from_text(
        user_input, st.session_state.student_context, api_key
    )
    new_res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
    st.session_state.last_result = new_res
    st.session_state.messages.append({"role": "assistant", "content": new_res["agent_message"]})
    st.rerun()

# Mostrar tarjetas limpias en español
res = st.session_state.last_result
if res and res["status"] == "recommendations_ready":
    ctx = res["context"]
    dist_clean = DISTRICT_LABELS.get(ctx["district_id"], ctx["district_id"])
    inst_clean = INSTITUTION_LABELS.get(ctx["institution_id"], ctx["institution_id"])
    horario_clean = "Vespertino (>18:00 hrs) o Sábados" if ctx["after_18h_or_weekend"] else "Horario flexible"

    st.markdown("### ✦ Oportunidades recomendadas para ti")
    st.info(
        f"**Perfil interpretado:** 📍 {dist_clean}  |  🏫 {inst_clean}  |  🕐 {horario_clean}"
    )

    st.markdown("#### 👥 Espacios permanentes para compartir entre pares")
    s_cols = st.columns(max(1, len(res["peer_services"])))
    for idx, srv in enumerate(res["peer_services"]):
        with s_cols[idx]:
            with st.container(border=True):
                st.markdown(f"### {srv['name']}")
                st.markdown(f"**{SERVICE_TYPE_LABELS.get(srv['service_type'], srv['service_type'])}**")
                st.write(f"📍 **Ubicación:** {DISTRICT_LABELS.get(srv['district_id'], srv['district_id'])}")
                st.write(f"🕐 **Horario:** {format_schedule(srv['schedule'])}")
                st.write(f"💬 **Modalidad:** {format_channels(srv['channels'])} · 👥 **Cupos:** {srv['capacity']} personas")
                st.progress(min(srv["score"], 100) / 100, text=f"Compatibilidad con tu rutina: {srv['score']}%")
                st.markdown("**¿Por qué te lo recomendamos?**")
                for r in srv["reasons"]:
                    st.markdown(f"- ✓ {r}")
                st.caption(
                    f"Respaldo Data Pack: ID {srv['id']} (D6) · {srv['attendance_rate']}% de asistencia histórica en D2"
                )

    st.markdown("#### 📅 Próximos encuentros y actividades en tu calendario")
    e_cols = st.columns(max(1, len(res["events"])))
    for idx, ev in enumerate(res["events"]):
        with e_cols[idx]:
            with st.container(border=True):
                st.markdown(f"### {ev['title']}")
                st.markdown(f"**{EVENT_TYPE_LABELS.get(ev['event_type'], ev['event_type'])}**")
                st.write(f"📅 **Fecha:** {format_date_range(ev['start_date'], ev['end_date'])}")
                st.write(f"📍 **Lugar:** {DISTRICT_LABELS.get(ev['district_id'], ev['district_id'])}")
                st.write(f"🏫 **Organiza:** {INSTITUTION_LABELS.get(ev['institution_id'], ev['institution_id'])}")
                st.progress(min(ev["score"], 65) / 65, text=f"Afinidad institucional y territorial: {ev['score']}/65 pts")
                st.markdown("**¿Por qué te lo recomendamos?**")
                for r in ev["reasons"]:
                    st.markdown(f"- ✓ {r}")
                st.caption(f"Respaldo Data Pack: Evento {ev['id']} (D7_calendar)")

elif res and res["status"] == "referral_ready":
    st.warning(
        "🛡️ **Derivación Responsable a Apoyo Humano:** NEXO es un agente logístico y no realiza diagnósticos "
        "clínicos ni evaluaciones psicológicas. Te conectamos directamente con el equipo humano de tu distrito:"
    )
    r_cols = st.columns(max(1, len(res["referrals"])))
    for idx, ref in enumerate(res["referrals"]):
        with r_cols[idx]:
            with st.container(border=True):
                st.markdown(f"### {ref['name']}")
                st.markdown(f"**{SERVICE_TYPE_LABELS.get(ref['service_type'], ref['service_type'])}**")
                st.write(f"📍 **Ubicación:** {DISTRICT_LABELS.get(ref['district_id'], ref['district_id'])}")
                st.write(f"🕐 **Horario de atención:** {format_schedule(ref['schedule'])}")
                st.write(f"📞 **Canales disponibles:** {format_channels(ref['channels'])}")
                st.markdown(
                    f"- ✓ Atención realizada por personal e infraestructura oficial de Ciudad Aethera.\n"
                    f"- ✓ Tasa de asistencia efectiva del **{ref['attendance_rate']}%** (tiempo de espera mediano: {ref['median_wait_days']:.0f} días)."
                )
                st.caption(f"Respaldo Data Pack: Servicio {ref['service_id']} (D6_services_map + D2_support_services)")
