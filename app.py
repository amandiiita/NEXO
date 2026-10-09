import streamlit as st
from data_loader import load_all_data
from agent import extract_context_from_text, run_nexo

# 1. Configuración de página (Sin emojis, letra "N" como ícono de pestaña)
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

    /* Tarjetas de resultados (Contenedores) */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
        background: var(--secondary-background-color);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(150, 150, 150, 0.1);
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

# --- LÓGICA DE DATOS ---
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
    s = s.replace("Mon-Sat", "Lunes a sábado").replace("Mon-Fri", "Lunes a viernes")
    return f"{s} hrs"

def format_channels(raw_channels):
    c = str(raw_channels)
    c = c.replace("in_person", "Presencial").replace("phone", "Teléfono").replace("digital", "Online")
    return c

def format_date_range(start_str, end_str):
    try:
        if start_str == end_str:
            return start_str
        return f"{start_str} al {end_str}"
    except Exception:
        return f"{start_str} al {end_str}"

calendar, support_history, services = load_all_data()

if "student_context" not in st.session_state:
    st.session_state.student_context = {
        "goal": None, "district_id": None, "institution_id": None,
        "after_18h_or_weekend": False, "availability_confirmed": False
    }
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Barra lateral: Trazabilidad técnica (Limpia y sin emojis)
with st.sidebar:
    st.markdown("### Trazabilidad del Agente")
    st.caption("Estado interno estructurado por NEXO:")
    st.json(st.session_state.student_context)
    st.markdown("---")
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    # Indicador de Agente Activo con efecto de "respiración" (Glow/Pulse)
    st.markdown("""
        <style>
        /* Animación para que la luz palpite */
        @keyframes pulse-glow {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 170, 0.4); }
            70% { box-shadow: 0 0 0 8px rgba(0, 255, 170, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 170, 0); }
        }
        
        .status-dot {
            width: 8px; 
            height: 8px;
            background-color: #00FFAA; /* Verde neón estilo tech */
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 10px #00FFAA;
            animation: pulse-glow 2s infinite; /* Aquí le decimos que palpite infinito */
        }
        
        .status-container {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            background: rgba(0, 255, 170, 0.05);
            border: 1px solid rgba(0, 255, 170, 0.15);
            border-radius: 8px;
            margin-bottom: 15px;
        }
        </style>
        
        <div class="status-container">
            <div class="status-dot"></div>
            <span style="font-size: 0.85rem; font-weight: 500; color: var(--text-color); opacity: 0.8;">Agente Gemini Activo</span>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Reiniciar conversación", use_container_width=True):
        st.session_state.student_context = {
            "goal": None, "district_id": None, "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False
        }
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()

# Botones de demostración (Centrados y limpios)
st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Demo Conversacional", use_container_width=True):
        st.session_state.student_context = {
            "goal": None, "district_id": None, "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False
        }
        st.session_state.messages = []
        msg = "Quiero conocer gente en la universidad, pero trabajo y salgo después de las 18:00."
        st.session_state.messages.append({"role": "user", "content": msg})
        st.session_state.student_context = extract_context_from_text(msg, st.session_state.student_context, api_key)
        res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
        st.session_state.last_result = res
        st.session_state.messages.append({"role": "assistant", "content": res["agent_message"]})
        st.rerun()

with c2:
    if st.button("Demo Integración", use_container_width=True):
        st.session_state.student_context = {
            "goal": None, "district_id": None, "institution_id": None,
            "after_18h_or_weekend": False, "availability_confirmed": False
        }
        st.session_state.messages = []
        msg = "Estudio en Nova Aether, me muevo por Nebula, trabajo y quiero conocer gente después de las 18:00."
        st.session_state.messages.append({"role": "user", "content": msg})
        st.session_state.student_context = extract_context_from_text(msg, st.session_state.student_context, api_key)
        res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
        st.session_state.last_result = res
        st.session_state.messages.append({"role": "assistant", "content": res["agent_message"]})
        st.rerun()

with c3:
    if st.button("Demo Derivación", use_container_width=True):
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

st.markdown("<br><br>", unsafe_allow_html=True)

# Flujo del chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# Interacciones del agente
res = st.session_state.last_result
if res and res["status"] == "needs_info":
    missing = res.get("missing_field")
    if missing == "district_id":
        st.caption("Selecciona tu distrito:")
        d_cols = st.columns(5)
        for idx, (label, code) in enumerate([
            ("Nébula", "DIST_NEBULA"), ("Gaia", "DIST_GAIA"),
            ("Vector", "DIST_VECTOR"), ("Horizonte", "DIST_HORIZON"),
            ("Quantum", "DIST_QUANTUM")
        ]):
            if d_cols[idx].button(label, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": label})
                st.session_state.student_context["district_id"] = code
                new_res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
                st.session_state.last_result = new_res
                st.session_state.messages.append({"role": "assistant", "content": new_res["agent_message"]})
                st.rerun()

    elif missing == "institution_id":
        st.caption("Selecciona tu institución:")
        i_cols = st.columns(3)
        for idx, (label, code) in enumerate([
            ("Nova Aether", "UNI_NOVA_AETHER"),
            ("Instituto Nexus", "INST_NEXUS"),
            ("Universidad Horizonte", "UNI_HORIZONTE")
        ]):
            if i_cols[idx].button(label, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": label})
                st.session_state.student_context["institution_id"] = code
                new_res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
                st.session_state.last_result = new_res
                st.session_state.messages.append({"role": "assistant", "content": new_res["agent_message"]})
                st.rerun()

user_input = st.chat_input("Escribe tu consulta aquí...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.student_context = extract_context_from_text(
        user_input, st.session_state.student_context, api_key
    )
    new_res = run_nexo(calendar, services, support_history, st.session_state.student_context, api_key)
    st.session_state.last_result = new_res
    st.session_state.messages.append({"role": "assistant", "content": new_res["agent_message"]})
    st.rerun()

# Tarjetas de resultados
if res and res["status"] == "recommendations_ready":
    ctx = res["context"]
    dist_clean = DISTRICT_LABELS.get(ctx["district_id"], ctx["district_id"])
    inst_clean = INSTITUTION_LABELS.get(ctx["institution_id"], ctx["institution_id"])
    horario_clean = "Vespertino o Sábados" if ctx["after_18h_or_weekend"] else "Horario flexible"

    st.markdown("---")
    st.markdown("### Oportunidades recomendadas")
    st.caption(f"Perfil: {dist_clean} | {inst_clean} | {horario_clean}")

    if res["peer_services"]:
        st.markdown("<br>#### Espacios permanentes", unsafe_allow_html=True)
        s_cols = st.columns(max(1, len(res["peer_services"])))
        for idx, srv in enumerate(res["peer_services"]):
            with s_cols[idx]:
                with st.container():
                    st.markdown(f"**{srv['name']}**")
                    st.caption(SERVICE_TYPE_LABELS.get(srv['service_type'], srv['service_type']))
                    st.write(f"Ubicación: {DISTRICT_LABELS.get(srv['district_id'], srv['district_id'])}")
                    st.write(f"Horario: {format_schedule(srv['schedule'])}")
                    st.write(f"Modalidad: {format_channels(srv['channels'])} | Cupos: {srv['capacity']}")
                    for r in srv["reasons"]:
                        st.markdown(f"- {r}")

    if res["events"]:
        st.markdown("<br>#### Próximos eventos", unsafe_allow_html=True)
        e_cols = st.columns(max(1, len(res["events"])))
        for idx, ev in enumerate(res["events"]):
            with e_cols[idx]:
                with st.container():
                    st.markdown(f"**{ev['title']}**")
                    st.caption(EVENT_TYPE_LABELS.get(ev['event_type'], ev['event_type']))
                    st.write(f"Fecha: {format_date_range(ev['start_date'], ev['end_date'])}")
                    st.write(f"Lugar: {DISTRICT_LABELS.get(ev['district_id'], ev['district_id'])}")
                    st.write(f"Organiza: {INSTITUTION_LABELS.get(ev['institution_id'], ev['institution_id'])}")
                    for r in ev["reasons"]:
                        st.markdown(f"- {r}")

elif res and res["status"] == "referral_ready":
    st.markdown("---")
    st.markdown("### Derivación de Apoyo")
    st.caption("NEXO no realiza diagnósticos clínicos. Te conectamos con el equipo de tu distrito.")
    r_cols = st.columns(max(1, len(res["referrals"])))
    for idx, ref in enumerate(res["referrals"]):
        with r_cols[idx]:
            with st.container():
                st.markdown(f"**{ref['name']}**")
                st.caption(SERVICE_TYPE_LABELS.get(ref['service_type'], ref['service_type']))
                st.write(f"Ubicación: {DISTRICT_LABELS.get(ref['district_id'], ref['district_id'])}")
                st.write(f"Atención: {format_schedule(ref['schedule'])}")
                st.write(f"Canales: {format_channels(ref['channels'])}")