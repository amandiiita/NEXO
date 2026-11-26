"""Casos de borde con datos del ZIP, sin modelos reales."""
import json
import os
import unittest
from unittest.mock import patch
import nexo_model as n
from pruebas.chat import Chat
from pruebas.test_arquitectura import plan,resp
from pruebas.test_interfaz import FULL,modelos

class Limites(unittest.TestCase):
    def test_cambio_referente(self):
        """El nombre en la pregunta de participación prevalece sobre la tarjeta anterior."""
        with patch.dict(os.environ,{"NEXO_MODO":"reglas"}):
            c=Chat().say(FULL).say("¿Cómo puedo participar en Espacio Trama Pares?")
            self.assertEqual(c.last["card"]["title"],"Espacio Trama Pares");self.assertEqual(c.state["context"]["district_id"],"DIST_NEBULA")

    def test_d7_desde_chat_vacio(self):
        """Localiza una actividad nombrada en D7 aun sin perfil previo."""
        with patch.dict(os.environ,{"NEXO_MODO":"reglas"}):
            c=Chat().say("¿A qué hora es Semana de pausa y bienestar 4?")
            self.assertIn("30 nov 2026",c.last["content"]);self.assertIn("no registra una hora",c.last["content"])
            self.assertEqual(c.state["traza"]["registros"],["CAL_AE_0028"])

    def test_recurso_inexistente(self):
        """Un espacio que no figura en D6 no hereda la dirección del seleccionado."""
        with patch.dict(os.environ,{"NEXO_MODO":"reglas"}):
            c=Chat().say(FULL).say("¿Cuál es la dirección de Espacio Inventado?")
            self.assertIn("¿De qué espacio",c.last["content"]);self.assertNotIn("Lumen",c.last["content"])

    def test_seguimiento_libre(self):
        """El modelo formula una invitación nueva vinculada a un botón real."""
        def fake(name,phase,entry):
            if phase=="plan":return plan()
            return {**resp(entry),"pregunta":"¿Te gustaría revisar cómo participar?"}
        with modelos(fake):
            c=Chat().say(FULL);self.assertIn("¿Te gustaría revisar cómo participar?",c.last["content"])
            self.assertIn("Cómo participar",[x[0] for x in c.last["actions"]])

    def test_ordenar_hechos(self):
        """El redactor puede priorizar los cupos antes del teléfono sin perder campos ni el siguiente paso."""
        def fake(name,phase,entry):
            if phase=="plan":return plan("consultar_ficha",["telefono","cupos"]) if "teléfono" in entry["mensaje"] else plan()
            out=resp(entry)
            if len(out["evidencias"])==3:out["evidencias"]=["E2","E1","E3"]
            return out
        with modelos(fake):
            c=Chat().say(FULL).say("¿Cuál es el teléfono y cuántos cupos quedan?")
            txt=c.last["content"]
            self.assertLess(txt.index("cupos"),txt.index("número oficial"))
            self.assertEqual(txt.count("Consulta a tu institución"),1)

    def test_horario_impreciso(self):
        """Una franja vaga sustituye la disponibilidad antigua por una pregunta, sin inventar horas."""
        def fake(name,phase,entry):
            if phase=="plan" and "merienda" in entry["mensaje"]:return plan("actualizar_perfil",franja="después de merendar")
            return plan() if phase=="plan" else resp(entry)
        with modelos(fake):
            c=Chat().say(FULL).say("En realidad mi merienda cambia, solo después de merendar")
            self.assertIsNone(c.state["availability"]);self.assertEqual(c.state["waiting"],"availability")
            self.assertEqual(c.state["context"]["district_id"],"DIST_NEBULA")

    def test_ayuda_entre_estudiantes(self):
        """Buscar un grupo de estudio continúa siendo una necesidad de integración."""
        with patch.dict(os.environ,{"NEXO_MODO":"reglas"}):
            c=Chat().say("Busco un grupo para estudiar cálculo")
            self.assertEqual(c.state["waiting"],"availability");self.assertFalse(c.state["scope_pending"])

    def test_contexto_largo_nube(self):
        """La memoria enviada sigue acotada en un diálogo largo y conserva el referente institucional."""
        seen=[]
        def fake(name,phase,entry):
            if phase=="plan":seen.append(entry);return plan("explicar") if "ese espacio" in entry["mensaje"] else plan()
            return resp(entry)
        with modelos(fake):
            c=Chat().say(FULL)
            for _ in range(7):c.say("¿Por qué me recomiendas ese espacio?")
            self.assertEqual(seen[-1]["memoria"]["seleccion"],"Espacio Lumen Pares")
            self.assertEqual(len(seen[-1]["memoria"]["ultimas_acciones"]),4)
            self.assertNotIn("messages",seen[-1]);self.assertEqual(len(c.state["messages"]),16)

