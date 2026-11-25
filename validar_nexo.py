"""Matriz de comportamiento de NEXO. Ejecutar desde la raíz de la app."""
import json
import os
from pathlib import Path
import sys
import types
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path.cwd()))
import agent
import data_loader

FULL = "Estudio en Nova Aether, me muevo por Nébula y quiero conocer gente después de las 18."
VECTOR = "Estudio en Instituto Nexus, vivo en Vector y quiero conocer gente después de las 18."
SUPPORT = "Me siento muy mal y necesito hablar con alguien en Nébula."
SUNDAY = "Vivo en Nébula, estudio en Nova Aether y quiero conocer gente. Solo puedo los domingos."
ACADEMIC = "¿Me explicas cómo hacer una derivada?"
ADDRESS = "¿Cuál es la dirección exacta de Espacio Trama Pares?"
CASES = []


def scenario(entry, expected, correction):
    def register(func):
        CASES.append((entry, expected, correction, func))
        return func
    return register


class Chat:
    def __init__(self):
        self.at = AppTest.from_file(str(Path.cwd() / "app.py"), default_timeout=15).run()
        self.evidence = ""

    @property
    def state(self):
        return self.at.session_state["nexo"]

    def run(self, pending):
        pending.run()
        errors = [item.message for item in self.at.exception]
        if errors:
            raise AssertionError(f"Excepción visible: {errors[0]}")
        if self.at.chat_message:
            turn = self.at.chat_message[-1]
            self.evidence = " ".join(str(el.value) for group in (turn.text, turn.markdown, turn.caption) for el in group)
        else:
            self.evidence = "Chat vacío"
        return self

    def say(self, text):
        return self.run(self.at.chat_input[0].set_value(text))

    def press(self, label, index=0):
        options = [b for b in self.at.button if b.label == label]
        assert len(options) > index, f"Botón ausente: {label}."
        return self.run(options[index].click())

    def sees(self, *strings):
        assert all(s.casefold() in self.evidence.casefold() for s in strings), (
            f"Faltó «{next(s for s in strings if s.casefold() not in self.evidence.casefold())}».")
        return self

    def slot(self, days, start, end):
        expected = (days, start, end)
        assert self.state["availability"] == expected, f"Disponibilidad observada: {self.state['availability']!r}."
        self.evidence = f"Disponibilidad confirmada: {self.state['availability']!r}. " + self.evidence
        return self


@scenario("Consulta completa en Nébula", "Espacio Lumen Pares con horario publicado.", "Recorrido conservado.")
def full(c): c.say(FULL).sees("Espacio Lumen Pares", "12:00 a 20:00")


@scenario("Consulta completa en Vector", "Espacio Trama Pares.", "Recorrido conservado.")
def vector(c): c.say(VECTOR).sees("Espacio Trama Pares")


@scenario("Quiero conocer gente", "Pide solo el horario.", "Recorrido conservado.")
def incomplete(c): c.say("Quiero conocer gente").sees("¿Cuándo puedes participar?")


@scenario("Estudio en Nova Aether, me muevo por Nébula, trabajo durante el día y quiero conocer gente", "Pide disponibilidad y conserva distrito e institución.", "Distinguir turno de trabajo de tiempo libre.")
def day_job(c):
    c.say("Estudio en Nova Aether, me muevo por Nébula, trabajo durante el día y quiero conocer gente").sees("¿Cuándo puedes participar?")
    assert c.state["context"]["district_id"] == "DIST_NEBULA" and c.state["context"]["institution_id"] == "UNI_NOVA_AETHER"


@scenario("Quiero conocer gente, pero trabajo de 9 a 18 → sí", "Confirma primero y acepta solo después de las 18.", "Separar rangos laborales de ventanas de participación.")
def work_range(c):
    c.say("Quiero conocer gente, pero trabajo de 9 a 18").sees("trabajas hasta las 18:00")
    assert c.state["availability"] is None
    c.say("sí").slot(tuple(range(7)), 1080, 1440)


@scenario("Trabajo hasta las 18 → no", "Pide otro horario, sin confirmar el sugerido.", "Recorrido conservado.")
def work_no(c):
    c.say("Trabajo hasta las 18").sees("¿Puedes participar después")
    c.say("no").sees("¿Cuándo puedes participar?")
    assert not c.state["availability"]


@scenario("Trabajo de 9 a 18, pero puedo los sábados", "Sábado completo; el turno no se toma como disponibilidad.", "Priorizar la cláusula explícita.")
def explicit_day(c):
    c.say("Quiero conocer gente. Trabajo de 9 a 18, pero puedo los sábados").slot((5,), 0, 1440)


@scenario("Después de las seis → 18:00", "Pregunta 06:00 o 18:00 y usa el horario elegido.", "Recorrido conservado.")
def time_ambiguity(c):
    c.say("Puedo después de las seis").sees("06:00 o a las 18:00")
    c.say("18:00").slot(tuple(range(7)), 1080, 1440)


@scenario("Después de las seis de la tarde", "Interpreta 18:00.", "Recorrido conservado.")
def time_part(c): c.say("Quiero conocer gente después de las seis de la tarde").slot(tuple(range(7)), 1080, 1440)


@scenario("No puedo después de las 18, solo los sábados", "Sábado hasta las 18:00.", "Cruzar la restricción negativa con los días permitidos.")
def negative(c): c.say("No puedo después de las 18, solo los sábados").slot((5,), 0, 1080)


@scenario("Sábado después de las 18 → «No puedo después de las 18»", "Pide un horario válido y revisa la restricción anterior.", "Evitar recomendar con disponibilidad invalidada.")
def invalidated(c):
    c.say(FULL).say("Solo puedo los sábados después de las 18").say("No puedo después de las 18").sees("¿Cuándo puedes participar?")
    assert c.state["availability"] is None


@scenario("No puedo los domingos, pero sí el fin de semana", "Conserva sábado y excluye domingo.", "Excluir días declarados como no disponibles.")
def days(c): c.say("No puedo los domingos, pero sí el fin de semana").slot((5,), 0, 1440)


@scenario("Cambiar de Nébula a Vector", "Trama Pares y misma institución/horario.", "Recorrido conservado.")
def change_district(c):
    c.say(FULL).say("Quiero cambiar de distrito").say("Vector").sees("Espacio Trama Pares")
    assert c.state["context"]["institution_id"] == "UNI_NOVA_AETHER"
    c.slot(tuple(range(7)), 1080, 1440)


@scenario("Cambiar a sábados en Nébula", "Nueva disponibilidad y mismo distrito.", "Recorrido conservado.")
def change_time(c):
    c.say(FULL).say("¿Y si solo puedo los sábados?").sees("Espacio Lumen Pares")
    c.slot((5,), 0, 1440)


@scenario("¿Dónde queda?", "Nombre y distrito de la opción activa.", "Recorrido conservado.")
def location(c): c.say(FULL).say("¿Dónde queda?").sees("Espacio Lumen Pares figura en Nébula")


@scenario("¿En qué horario funciona?", "Horario documentado del espacio actual.", "Ampliar expresiones de seguimiento.")
def schedule(c): c.say(FULL).say("¿En qué horario funciona?").sees("El horario publicado", "12:00 a 20:00")


@scenario("Dirección exacta de Trama Pares con chat vacío", "Vector; avisa que D6 no tiene la dirección.", "Búsqueda nominal conservada.")
def address(c): c.say(ADDRESS).sees("Espacio Trama Pares figura en Vector", "no incluye la dirección exacta")


@scenario("¿Y el teléfono?", "Aclara que el número oficial no figura.", "Distinguir tipo de canal de contacto concreto.")
def phone(c): c.say(VECTOR).say("¿Y el teléfono?").sees("El catálogo no confirma el número oficial")


@scenario("¿Hay cupos?", "Avisa que no hay inventario actualizado.", "No inferir cupos a partir de capacidad nominal.")
def seats(c): c.say(VECTOR).say("¿Hay cupos?").sees("no confirma si hay cupos disponibles")


@scenario("¿Hay que inscribirse?", "Explica que el requisito no figura.", "Distinguir inscripción de canales.")
def signup(c): c.say(VECTOR).say("¿Hay que inscribirse?").sees("no confirma si necesitas inscribirte")


@scenario("Cómo participar → Guardar próximo paso", "Canales, hora, próximo paso y duración en sesión.", "Comunicar la persistencia real del guardado.")
def save(c):
    c.say(VECTOR).press("Cómo participar").sees("Presencial y Teléfono", "Tu próximo paso").press("Guardar próximo paso").sees("durante esta sesión")
    assert c.state["saved"]["title"] == "Espacio Trama Pares"


@scenario("Repetir «guarda»", "Conserva un plan; confirma que ya estaba guardado.", "Guardado idempotente.")
def save_again(c):
    c.say(VECTOR).say("guarda").say("guarda").sees("ya está guardado")
    assert c.state["saved"]["title"] == "Espacio Trama Pares"


@scenario("¿Hay otra opción?", "Avanza de Lumen a Brújula.", "Recorrido conservado.")
def other(c): c.say(FULL).say("¿Hay otra opción?").sees("Espacio Brújula Pares")


@scenario("¿Por qué me recomiendas esta?", "Criterios respaldados por D6.", "Recorrido de motivos conservado.")
def why(c): c.say(FULL).say("¿Por qué me recomiendas esta?").sees("distrito que indicaste", "D6")


@scenario("¿Me explicas cómo hacer una derivada? → Sí", "Reconoce el límite y abre búsqueda de actividades.", "Recorrido de redirección conservado.")
def academic(c):
    c.say(ACADEMIC).sees("No puedo resolver ejercicios académicos").say("Sí").sees("¿Cuándo puedes participar?")
    assert c.state["search_kind"] == "events"


@scenario("Receta de pasta → No", "Declina y acepta la negativa.", "Recorrido fuera de ámbito conservado.")
def scope_no(c): c.say("Dame una receta de pasta").sees("fuera del ámbito").say("No").sees("De acuerdo")


@scenario("Sí en un chat vacío", "Aclara qué quiere buscar.", "No usar un «sí» sin antecedente.")
def yes_empty(c): c.say("Sí").sees("¿Buscas una actividad")


@scenario("Solo domingos, perfil completo", "Sin espacios publicados; conserva preferencias.", "Acotar la cobertura a D6.")
def sunday(c):
    c.say(SUNDAY).sees("No encontré espacios de pares compatibles en Nébula", "domingo", "otros distritos")
    assert not c.state["result"]["peers"]


@scenario("Solo domingos → Ver actividades", "Aclara que las fechas vigentes no coinciden con ese día.", "Separar días del evento y horas de atención.")
def dated(c): c.say(SUNDAY).press("Ver actividades").sees("no coinciden con tus días indicados", "La hora exacta")


@scenario("Me interesa el bienestar, perfil completo", "Encuentra la actividad cuyo título menciona bienestar.", "Usar intereses con respaldo documental.")
def interest(c):
    c.say(FULL).say("Me interesa el bienestar").sees("mencionan tu interés", "Semana de pausa y bienestar 4")


@scenario("¿Algo con mis intereses? → fútbol", "Pide el interés y señala que no hay una coincidencia documentada.", "Conservar perfil y distinguir falta de evidencia.")
def interest_unmatched(c):
    c.say(FULL).say("¿Puedes buscar algo con mis intereses?").sees("¿Qué te interesa?")
    c.say("fútbol").sees("No encontré una coincidencia documentada para deporte", "actividades generales")
    assert c.state["context"]["district_id"] == "DIST_NEBULA"


@scenario("Me siento mal → Vector", "Orienta hacia apoyo humano e identifica la simulación y el límite clínico.", "Explicitar el tipo y alcance del recurso.")
def support(c):
    c.say("Me siento mal y necesito hablar con alguien").sees("¿En qué distrito buscas apoyo?")
    c.say("Vector").sees("Espacio Trama Orientación", "demostración", "atención clínica")


@scenario("Frase explícita de peligro inmediato", "Emergencias reales y apoyo cercano; sin búsqueda en el catálogo.", "Respuesta directa conservada.")
def urgent(c):
    c.say("Me voy a hacer daño ahora").sees("servicios de emergencia", "persona de confianza")
    assert not c.state["sources"]


@scenario("Calendario en el escenario del 23 de noviembre", "Diferencia fechas pasadas y la actividad vigente.", "Fecha de simulación y avisos conservados.")
def dates(c): c.say(FULL).press("Ver actividades").sees("23 nov 2026", "Fecha pasada", "Semana de pausa")


@scenario("Reiniciar después de guardar", "Elimina tarjeta guardada y sesión del chat.", "Recorrido conservado.")
def reset(c):
    c.say(VECTOR).say("guarda").press("Reiniciar conversación").sees("Chat vacío")
    assert not c.state["saved"]


@scenario("Demo Conversacional con botones", "Distrito → institución → Lumen → Cómo participar.", "Entrada de demostración conservada.")
def demo(c):
    c.press("Demo Conversacional").press("Nébula").press("Universidad Nova Aether").sees("Espacio Lumen Pares")
    c.press("Cómo participar").sees("Tu próximo paso")


@scenario("Identificación real de pares y orientación", "Los objetos traen service_id canónico y se cruzan con D6.", "Unificar clave y preservar alias id.")
def ids(c):
    calendar, history, services = data_loader.load_all_data()
    context = {"goal": "social_connection", "district_id": "DIST_NEBULA", "institution_id": "UNI_NOVA_AETHER", "availability_confirmed": True}
    peers = agent.run_nexo(calendar, services, history, context)["peer_services"]
    support = agent.run_nexo(calendar, services, history, {**context, "goal": "human_support"})["referrals"]
    assert peers and support and all(i.get("service_id") in set(services["service_id"]) for i in peers + support), "Una rama no trae service_id."
    c.evidence = f"D6 cruzado con {len(peers)} pares y {len(support)} referencias; todos con service_id."


@scenario("Repetir búsqueda y preguntar motivo", "Una sola consulta al motor con la misma firma.", "Reutilizar resultados de la sesión.")
def cache(c):
    with patch.object(agent, "run_nexo", wraps=agent.run_nexo) as call:
        c.at.run()
        c.say(FULL).say(FULL).say("¿Por qué esta opción?")
        assert call.call_count == 1, f"Consultas al motor: {call.call_count}."
        c.evidence = f"Consultas al motor: {call.call_count}; el motivo sigue disponible."


@scenario("Fallo de datos puntual → Volver a intentar", "Mensaje legible y recuperación con la misma consulta.", "Capturar fallos después de interpretar y restaurar estado.")
def recover(c):
    loader = data_loader.load_all_data
    st.cache_data.clear()
    with patch.object(data_loader, "load_all_data", side_effect=[TypeError("diagnóstico privado de prueba"), loader()]):
        c.at.run()
        c.say(FULL).sees("Conservé los datos de tu búsqueda")
        assert "diagnóstico privado" not in c.evidence
        c.press("Volver a intentar").sees("Espacio Lumen Pares")


def simulate_gemini(answer):
    sent = []
    google = types.ModuleType("google")
    genai = types.ModuleType("google.genai")
    def generate(**kwargs):
        sent.append(kwargs)
        if isinstance(answer, Exception):
            raise answer
        body = answer if isinstance(answer, dict) else {"intent": answer}
        raw = answer.decode() if isinstance(answer, bytes) else json.dumps(body)
        return types.SimpleNamespace(text=raw, model_version="gemini-prueba")
    client = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=generate))
    genai.Client = lambda **kwargs: type("Client", (), {
        "models": client.models, "__enter__": lambda self: client, "__exit__": lambda self, *args: None})()
    genai.types = types.SimpleNamespace(**{name: dict for name in (
        "GenerateContentConfig", "HttpOptions", "HttpRetryOptions")})
    google.genai = genai
    return patch.dict(sys.modules, {"google": google, "google.genai": genai}), sent


@scenario("Consulta abierta sin credenciales", "Pide aclaración local y no requiere API.", "Distinguir ambigüedad de consulta ajena.")
def offline(c):
    c.say("Me gustaría sentirme parte de este nuevo lugar").sees("¿Buscas una actividad")
    assert c.state["interpretation"] == "Reglas de NEXO"


@scenario("Gemini devuelve una intención válida (SDK simulado)", "Usa intención y registra versión devuelta.", "Trazabilidad por turno con modelo efectivo.")
def model_ok(c):
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini("social_connection")
    with context:
        c.say("Me gustaría sentirme parte de este nuevo lugar").sees("¿Cuándo puedes participar?")
    assert len(sent) == 1 and "gemini-prueba" in c.state["interpretation"], c.state["interpretation"]
    c.evidence = c.state["interpretation"] + ". " + c.evidence


@scenario("Gemini falla con 503 (SDK simulado)", "Una llamada; recuperación por reglas y sin código visible.", "Límite de tiempo, sin reintentos y ruta local.")
def model_error(c):
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini(RuntimeError("503 diagnóstico privado de prueba"))
    with context:
        c.say("Me gustaría sentirme parte de este nuevo lugar").sees("¿Buscas una actividad")
    assert len(sent) == 1 and "respuesta por reglas" in c.state["interpretation"] and "503" not in c.evidence
    c.evidence = c.state["interpretation"] + ". " + c.evidence


@scenario("Gemini devuelve una etiqueta inválida (SDK simulado)", "Rechaza etiqueta y pide aclaración.", "Validar contrato antes de actuar.")
def model_invalid(c):
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini("inventar_contacto")
    with context:
        c.say("Me gustaría sentirme parte de este nuevo lugar").sees("¿Buscas una actividad")
    assert len(sent) == 1 and "respuesta por reglas" in c.state["interpretation"] and not c.state["result"]


@scenario("Horario inválido en catálogo", "Valida minutos y orden del intervalo.", "Distinguir horario desconocido de coincidencia.")
def malformed_schedule(c):
    import ast
    tree = ast.parse(Path("app.py").read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ("read_schedule", "minutes")]
    env = {"re": __import__("re"), "DAYS": ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"),
           "DATAPACK_DAYS": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app.py", "exec"), env)
    assert env["read_schedule"]("Mon-Sat 16:90-20:00") is None, "Se aceptó minuto inválido."
    assert env["read_schedule"]("Mon-Sat 20:00-12:00") is None, "Se aceptó rango invertido."
    c.evidence = "Ambos horarios inválidos fueron rechazados."


@scenario("Demo Conversacional → distrito → institución → cómo participar → guardar", "Un intento de IA por turno y botones fieles a su acción.", "Pasar todas las entradas conversacionales por el mismo flujo.")
def demo_with_ai(c):
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini({"intent": "activities", "style": "orientador"})
    with context:
        c.press("Demo Conversacional").sees("¿En qué distrito quieres que busque primero?")
        c.press("Nébula").sees("Dime en qué institución")
        c.press("Universidad Nova Aether").sees("La primera opción de la búsqueda está en Nébula", "Espacio Lumen Pares")
        c.press("Cómo participar").sees("Empieza por estos datos", "Tu próximo paso")
        c.press("Guardar próximo paso").sees("Guardé este plan durante la sesión")
    chosen = [json.loads(call["contents"])["accion_elegida_en_la_interfaz"] for call in sent]
    assert chosen == ["demo", "district_id", "institution_id", "how", "save"], chosen
    assert c.state["saved"]["title"] == "Espacio Lumen Pares"
    assert "Variante orientador seleccionada por Gemini" in c.state["ai_output"]


@scenario("Gemini propone apoyo emocional para una búsqueda explícita de pares", "Conserva la intención explícita y marca la propuesta como tal.", "Aplicar validación local antes de desviar el flujo.")
def explicit_context_wins(c):
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini({"intent": "human_support", "style": "cercano"})
    with context:
        c.say(FULL).sees("Te propongo partir", "Espacio Lumen Pares")
    assert len(sent) == 1
    assert c.state["context"]["goal"] == "social_connection"
    assert "intención propuesta: human_support" in c.state["interpretation"]


@scenario("Gemini devuelve otro objetivo tras una restricción negativa", "Hace valer la disponibilidad explícita.", "Mantener el cruce real de horarios.")
def preserve_schedule(c):
    c.say(FULL)
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini({"intent": "why", "style": "directo"})
    with context:
        c.say("No puedo después de las 18, solo los sábados").slot((5,), 0, 1080)
    assert len(sent) == 1 and c.state["selected"]["title"] == "Espacio Lumen Pares"


@scenario("Respuesta JSON rota al pulsar Cómo participar", "Usa la tarjeta local en ese mismo turno.", "Vincular la recuperación al recorrido normal.")
def invalid_button(c):
    c.say(FULL)
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini(b"{JSON")
    with context:
        c.press("Cómo participar").sees("Tu próximo paso", "Presencial y Teléfono")
    assert len(sent) == 1 and "respuesta por reglas" in c.state["interpretation"]
    assert "{JSON" not in c.evidence


@scenario("Dos fallos, nuevo demo y fin de pausa", "Usa reglas durante la pausa y vuelve a intentar después.", "Preservar el estado del proveedor al reiniciar el chat.")
def circuit_recovers(c):
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, failed = simulate_gemini(RuntimeError("servicio caído en la prueba"))
    with context:
        c.press("Demo Conversacional").press("Nébula").press("Demo Integración").sees("Espacio Lumen Pares")
    assert len(failed) == 2 and "pausa automática" in c.state["interpretation"]
    c.state["ai_backoff_until"] = 0
    context, recovered = simulate_gemini({"intent": "schedule", "style": "directo"})
    with context:
        c.say("¿Cuál es la franja que anuncian?").sees("El horario publicado", "12:00 a 20:00")
    assert len(recovered) == 1 and c.state["ai_failures"] == 0


@scenario("Apoyo y emergencia en el chat, con clave configurada", "Respuestas de seguridad y orientación locales, sin llamada externa.", "Proteger el flujo de apoyo humano y conservar el acceso.")
def private_support(c):
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini("social_connection")
    with context:
        c.say(SUPPORT).sees("Espacio Lumen Orientación")
        c.press("Ver canales de atención").sees("Tu próximo paso")
        c.say("Me voy a hacer daño ahora").sees("servicios de emergencia")
    assert not sent and "Protocolo local de seguridad" in c.state["interpretation"]


@scenario("Consulta de seguimiento con nombre distinto del seleccionado", "Responde por Trama Pares y deja de apuntar a Lumen.", "Comprobar en D6 el servicio mencionado por el estudiante.")
def named_ai_followup(c):
    c.say(FULL)
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini({"intent": "contact", "focus": "phone", "style": "directo"})
    with context:
        c.say("¿Cómo podría hablar directamente con el equipo de Espacio Trama Pares?").sees("no confirma el número oficial para Espacio Trama Pares")
    assert len(sent) == 1 and c.state["selected"]["title"] == "Espacio Trama Pares"


@scenario("Confirmación coloquial a una invitación pendiente", "Interpreta la confirmación y retoma el calendario.", "Usar intención contextual sin perder la pregunta pendiente.")
def colloquial_confirmation(c):
    c.say(ACADEMIC)
    c.at.secrets["GEMINI_API_KEY"] = "credencial-ficticia-de-prueba"
    context, sent = simulate_gemini("yes")
    with context:
        c.say("Eso me tinca, probemos").sees("¿Cuándo puedes participar?")
    assert len(sent) == 1 and c.state["search_kind"] == "events"
    assert json.loads(sent[0]["contents"])["confirmacion_pendiente"] == "invitacion"


def main():
    output = []
    os.environ.pop("GEMINI_API_KEY", None)
    for i, (entry, expected, correction, func) in enumerate(CASES, 1):
        c = Chat()
        error = None
        try:
            func(c)
        except (AssertionError, KeyError, IndexError, TypeError, ValueError) as exc:
            error = str(exc)
        output.append({"n": i, "entrada": entry, "esperado": expected, "observado": c.evidence,
                       "error": error, "correccion": correction})
    Path(sys.argv[1]).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [(r["n"], r["error"]) for r in output if r["error"] is not None]
    print(f"{len(output)-len(failed)}/{len(output)} escenarios aprobados.")
    for n, error in failed:
        print(f"{n:02d} {error}")


if __name__ == "__main__":
    main()
