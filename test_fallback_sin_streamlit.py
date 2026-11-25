"""Pruebas del motor sin inicializar Streamlit."""
import ast
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
from threading import BoundedSemaphore, Event
from time import monotonic
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
# Carga las dependencias antes de reemplazar temporalmente el módulo de UI.
import agent
import data_loader
import nexo_model


class Session(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value


class NoUI:
    def __init__(self):
        self.session_state = Session()
        self.secrets = {}
    def cache_data(self, **kwargs):
        return lambda func: func


def load_engine():
    fake = NoUI()
    module = types.ModuleType("streamlit")
    module.session_state = fake.session_state
    module.secrets = fake.secrets
    module.cache_data = fake.cache_data
    tree = ast.parse(Path(__file__).with_name("app.py").read_text())
    allowed = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom,
                                                               ast.FunctionDef, ast.Assign, ast.AnnAssign))
               and not (isinstance(node, ast.Assign) and any(
                   isinstance(t, ast.Name) and t.id == "state" for t in node.targets))]
    with patch.dict(sys.modules, {"streamlit": module}):
        engine = types.ModuleType("nexo_test_engine")
        exec(compile(ast.Module(body=allowed, type_ignores=[]), "app.py", "exec"), engine.__dict__)
    engine.new_conversation()
    return engine, fake


FULL = "Estudio en Nova Aether, me muevo por Nébula y quiero conocer gente después de las 18."


class TestNEXO(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("GEMINI_API_KEY", None)
        self.app, self.st = load_engine()

    def say(self, txt):
        self.app.record_user(txt)
        self.app.safe_turn(self.app.handle_text, (txt,), "retry_text", txt)
        return self.st.session_state.nexo

    def test_offline_full(self):
        s = self.say(FULL)
        self.assertIn("Espacio Lumen Pares", str(s["messages"][-1]["card"]))
        self.assertEqual(s["context"]["district_id"], "DIST_NEBULA")
        self.assertEqual(s["interpretation"], "Reglas de NEXO")

    def test_offline_work_not_availability(self):
        s = self.say("Estudio en Nova Aether y trabajo de 9 a 18, quiero conocer gente")
        self.assertIn("trabajas hasta las 18:00", s["messages"][-1]["content"])
        self.assertIsNone(s["availability"])

    def test_ai_first_on_explicit_request(self):
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        dummy = {"intent": "social_connection", "style": "cercano"}
        with patch.object(self.app, "interpret_turn", return_value=(dummy, "gemini-simulado", "used")) as called:
            s = self.say(FULL)
        self.assertEqual(called.call_count, 1)
        self.assertIn("Gemini · gemini-simulado", s["interpretation"])
        self.assertIn("Te propongo partir", s["messages"][-1]["content"])

    def test_ai_interprets_unrecognized_intent(self):
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        dummy = {"intent": "social_connection", "focus": "none", "interest": "none"}
        with patch.object(self.app, "interpret_turn", return_value=(dummy, "simulado", "used")):
            s = self.say("Quisiera sentirme parte de este nuevo lugar")
        self.assertEqual(s["waiting"], "availability")

    def test_ai_interprets_natural_followup(self):
        s = self.say(FULL)
        self.assertTrue(s["selected"])
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        dummy = {"intent": "why", "focus": "none", "interest": "none"}
        with patch.object(self.app, "interpret_turn", return_value=(dummy, "simulado", "used")):
            s = self.say("¿Con qué te quedaste al hacer la comparación?")
        self.assertIn("criterios que usé", s["messages"][-1]["content"])
        self.assertIn("intención utilizada: why", s["interpretation"])

    def test_ai_invalid_fallback(self):
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        with patch.object(self.app, "interpret_turn", return_value=(None, None, "invalid_response")):
            s = self.say(FULL)
        self.assertIsNotNone(s["selected"])
        self.assertIn("respuesta por reglas", s["interpretation"])

    def test_ai_503_and_circuit(self):
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        with patch.object(self.app, "interpret_turn", return_value=(None, None, "unavailable")) as calls:
            s = self.say("Quiero conocer gente")
            self.say("Me muevo por Nébula")
            self.say("Estudio en Nova Aether")
        self.assertEqual(calls.call_count, 2)
        self.assertIn("pausa automática", s["interpretation"])
        self.assertEqual(s["context"]["district_id"], "DIST_NEBULA")

    def test_danger_no_ai(self):
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        with patch.object(self.app, "interpret_turn") as calls:
            s = self.say("Me voy a hacer daño ahora")
        calls.assert_not_called()
        self.assertIn("servicios de emergencia", s["messages"][-1]["content"])

    def test_no_invented_contacts(self):
        s = self.say(FULL)
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        dummy = {"intent": "contact", "focus": "phone", "interest": "none"}
        with patch.object(self.app, "interpret_turn", return_value=(dummy, "simulado", "used")):
            s = self.say("¿Hay manera de llamarles?")
        self.assertIn("no confirma", s["messages"][-1]["content"])

    def test_safe_reply_fallback(self):
        self.say(FULL)
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        with patch.object(self.app, "interpret_turn", side_effect=RuntimeError("error privado del SDK")):
            s = self.say("¿Por qué elegiste este lugar?")
        self.assertIn("criterios que usé", s["messages"][-1]["content"])
        self.assertIn("respuesta por reglas", s["interpretation"])
        self.assertNotIn("error privado", s["messages"][-1]["content"])

    def test_transport_sdk_simulated(self):
        calls = []
        google = types.ModuleType("google")
        genai = types.ModuleType("google.genai")
        def generate(**kw):
            calls.append(kw)
            return types.SimpleNamespace(text='{"intent":"activities","focus":"none","interest":"none"}',
                                         model_version="gemini-3.8-flash-prueba")
        model_api = types.SimpleNamespace(generate_content=generate)
        class Client:
            def __init__(self, **kw):
                self.models = model_api
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        genai.Client = Client
        genai.types = types.SimpleNamespace(HttpOptions=lambda **kw: kw,
                      HttpRetryOptions=lambda **kw: kw, GenerateContentConfig=lambda **kw: kw)
        google.genai = genai
        with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
            payload, version, status = nexo_model.interpret_turn("Muéstrame actividades", "clave-simulada")
        self.assertEqual(status, "used")
        self.assertEqual(payload["intent"], "activities")
        self.assertEqual(version, "gemini-3.8-flash-prueba")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["config"]["response_mime_type"], "application/json")

    def test_model_rejects_unsupported_facts(self):
        with patch.object(nexo_model, "_generate", return_value=({"intro": "¡Te garantizo 10 cupos en Gaia!"}, "sim", "used")):
            intro, _, status = nexo_model.compose_intro("Puedes revisar alternativas", "dummy")
        self.assertIsNone(intro)
        self.assertEqual(status, "unsafe_response")

    def test_after_failure_returns_to_ai(self):
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        dummy = {"intent": "social_connection", "focus": "none", "interest": "none"}
        with patch.object(self.app, "interpret_turn", side_effect=[(None, None, "unavailable"), (dummy, "ok", "used")]):
            self.say("Quiero conocer gente")
            s = self.say("Me muevo por Nébula")
        self.assertIn("Gemini · ok", s["interpretation"])
        self.assertEqual(s["ai_failures"], 0)

    def test_offline_yes_and_time(self):
        s = self.say("Quiero conocer gente, trabajo de 9 a 18")
        self.assertIsNone(s["availability"])
        s = self.say("sí")
        self.assertEqual(s["availability"], (tuple(range(7)), 1080, 1440))

    def test_offline_negative_availability(self):
        s = self.say("No puedo después de las 18, solo los sábados, quiero conocer gente")
        self.assertEqual(s["availability"], ((5,), 0, 1080))

    def test_offline_support(self):
        s = self.say("Me siento mal y necesito hablar con alguien en Vector")
        self.assertEqual(s["context"]["goal"], "human_support")
        self.assertIn("Espacio Trama Orientación", str(s["messages"][-1]["card"]))

    def test_offline_sunday_no_results(self):
        s = self.say("Estudio en Nova Aether en Nébula, quiero conocer gente pero solo puedo los domingos")
        self.assertIn("No encontré espacios de pares", s["messages"][-1]["content"])

    def test_offline_outside_scope(self):
        s = self.say("¿Me ayudas a hacer una derivada?")
        self.assertIn("No puedo resolver ejercicios", s["messages"][-1]["content"])
        s = self.say("sí")
        self.assertEqual(s["search_kind"], "events")

    def test_offline_saving_is_only_session(self):
        self.say(FULL)
        s = self.say("Guarda el próximo paso")
        self.assertIn("durante esta sesión", s["messages"][-1]["content"])
        self.assertIsNotNone(s["saved"])
        self.app.new_conversation()
        self.assertIsNone(self.st.session_state.nexo["saved"])

    def test_ai_interest_when_not_literal(self):
        self.say(FULL)
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        dummy = {"intent": "interest", "focus": "none", "interest": "arte"}
        with patch.object(self.app, "interpret_turn", return_value=(dummy, "simulado", "used")):
            s = self.say("Quiero alguna actividad creativa")
        self.assertEqual(s["interest"], "arte")
        self.assertEqual(s["search_kind"], "events")

    def test_offline_exact_info_not_invented(self):
        self.say(FULL)
        s = self.say("¿Cuál es el teléfono?")
        self.assertIn("no confirma", s["messages"][-1]["content"])

    def test_compose_rejects_location_hallucination(self):
        with patch.object(nexo_model, "_generate", return_value=({"intro": "Puedes ir al recinto de Nébula cuando quieras"}, "sim", "used")):
            intro, _, status = nexo_model.compose_intro("El catálogo no informa direcciones", "dummy")
        self.assertIsNone(intro)
        self.assertEqual(status, "unsafe_response")

    def test_model_rejects_invalid_intent(self):
        with patch.object(nexo_model, "_generate", return_value=({"intent": "inventar_cupos", "focus": "none", "interest": "none"}, "sim", "used")):
            interpreted, _, status = nexo_model.interpret_turn("hay cupos?", "dummy")
        self.assertIsNone(interpreted)
        self.assertEqual(status, "invalid_response")

    def test_model_rejects_extra_facts(self):
        invalid = {"intent": "contact", "style": "directo", "address": "Dirección inventada"}
        with patch.object(nexo_model, "_generate", return_value=(invalid, "sim", "used")):
            plan, _, status = nexo_model.interpret_turn("adónde voy?", "dummy")
        self.assertIsNone(plan)
        self.assertEqual(status, "invalid_response")

    def test_request_excludes_history_and_obvious_contact_data(self):
        text = "Escríbeme a estudiante@aethera.example o +56 9 1234 5678. Mi RUT es 12345678-K."
        with patch.object(nexo_model, "_generate", return_value=({"intent": "out_of_context"}, "sim", "used")) as call:
            nexo_model.interpret_turn(text, "dummy", recent_messages=[{"role": "user", "content": "historial privado"}])
        request = json.dumps(call.call_args.args[2], ensure_ascii=False)
        self.assertNotIn("estudiante@", request)
        self.assertNotIn("5678", request)
        self.assertNotIn("historial privado", request)

    def test_wall_clock_timeout_does_not_delay_local_reply(self):
        entered, release = Event(), Event()

        def held_request(*args):
            entered.set()
            release.wait(3)
            return {"intent": "out_of_context"}, "tardío", "used"

        generate = nexo_model._generate
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        with patch.object(nexo_model, "_generate_once", side_effect=held_request), \
             patch.object(nexo_model, "_generate", side_effect=lambda *args: generate(*args, timeout_ms=35)):
            try:
                started = monotonic()
                state = self.say(FULL)
                self.assertTrue(entered.is_set())
                self.assertLess(monotonic() - started, 1.5)
                self.assertIn("se agotó el tiempo", state["interpretation"])
                self.assertEqual(state["selected"]["title"], "Espacio Lumen Pares")
            finally:
                release.set()
        self.assertEqual(state["selected"]["title"], "Espacio Lumen Pares")

    def test_capacity_is_bounded_during_hung_requests(self):
        entered, release = Event(), Event()
        with patch.object(nexo_model, "_SLOTS", BoundedSemaphore(1)), \
             ThreadPoolExecutor(max_workers=1) as pool, patch.object(nexo_model, "_POOL", pool):
            def held_request(*args):
                entered.set()
                release.wait(3)
                return None, None, "unavailable"
            with patch.object(nexo_model, "_generate_once", side_effect=held_request):
                try:
                    self.assertEqual(nexo_model._generate("dummy", "sim", {}, "", {}, 40)[2], "timeout")
                    self.assertTrue(entered.is_set())
                    self.assertEqual(nexo_model._generate("dummy", "sim", {}, "", {}, 40)[2], "busy")
                finally:
                    release.set()

    def test_quota_pauses_immediately_without_losing_search(self):
        self.st.secrets["GEMINI_API_KEY"] = "TEST_KEY"
        with patch.object(self.app, "interpret_turn", return_value=(None, None, "quota")) as model:
            state = self.say(FULL)
            self.assertEqual(state["selected"]["title"], "Espacio Lumen Pares")
            state = self.say("¿Dónde queda?")
        self.assertEqual(model.call_count, 1)
        self.assertIn("pausa automática", state["interpretation"])
        self.assertIn("figura en Nébula", state["messages"][-1]["content"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
