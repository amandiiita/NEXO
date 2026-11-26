"""Contratos REST, presupuestos, circuitos y composición con los adaptadores del producto."""
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
import time
import unittest
from unittest.mock import patch
import nexo_model as n
import proveedores as p
from entorno import comprobar

def plan(tool="buscar_pares",fields=(),ask="",interest="",franja=""):
    return {"herramienta":tool,"campos":list(fields),"preguntar":ask,"interes_literal":interest,"franja_literal":franja}

def resp(entry):
    q={"availability":"¿Qué horario te acomoda para participar?","district_id":"¿Por qué distrito te mueves?",
       "institution_id":"¿En qué universidad estudias?","interest":"¿Qué tema te interesa?"}
    return {"apertura":"Vamos a tu ritmo","evidencias":entry["obligatorias"],
            "pregunta":q.get(entry["campo_pregunta"],"")}

def configs(order="groq,ollama,gemini",**extra):
    values={"NEXO_PROVEEDORES":order,"GROQ_API_KEY":"prueba-sintetica","GEMINI_API_KEY":"prueba-sintetica",**extra}
    return p.configuracion(lambda k,d="":values.get(k,d))

def accept(value):
    return value if value=={"ok":True} else None

class Arquitectura(unittest.TestCase):
    def test_local_exclusivo(self):
        """Local excluye Groq y Gemini aun con claves y aunque el orden diga otra cosa."""
        services,_=configs("gemini,groq",NEXO_MODO="local")
        self.assertEqual([s.nombre for s in services],["ollama"])

    def test_orden(self):
        """Respeta el orden alternativo y evita proveedores repetidos."""
        services,_=configs("gemini,gemini,ollama,groq")
        self.assertEqual([s.nombre for s in services],["gemini","ollama","groq"])

    def test_config_falla_cerrada(self):
        """Modo desconocido desactiva la red y un timeout inválido recupera el valor de referencia."""
        self.assertFalse(configs(NEXO_MODO="desconocido")[0])
        self.assertEqual(configs(NEXO_TURNO_TIMEOUT="nan")[1],36)

    def test_credencial_ausente(self):
        """Una clave ausente se omite sin abrir conexión y se explica en la traza."""
        services,budget=configs(GROQ_API_KEY="")
        t=p.Turno(services,budget,{},transporte=lambda *_:'{"ok":true}')
        self.assertTrue(t.usar("plan","s",{}, {},accept))
        self.assertEqual([r["estado"] for r in t.intentos],["sin_clave","aceptado"])
        self.assertEqual(t.llamadas,1)

    def test_error_respuesta(self):
        """JSON roto y contenido inválido saltan al tercer modelo."""
        services,budget=configs()
        t=p.Turno(services,budget,{},transporte=lambda s,*_:{"groq":"{","ollama":"{}","gemini":'{"ok":true}'}[s.nombre])
        self.assertTrue(t.usar("plan","s",{}, {},accept))
        self.assertEqual([x["estado"] for x in t.intentos],["formato","restricciones","aceptado"])

    def test_cambio_de_redactor(self):
        """El resultado de la herramienta y la memoria son idénticos en ambos intentos de redacción."""
        calls=[]
        def transport(s,messages,schema,fase,timeout):
            calls.append((s.nombre,fase,messages))
            if fase=="respuesta" and s.nombre=="groq": raise p.Fallo("saturacion")
            return '{"ok":true}'
        services,budget=configs()
        t=p.Turno(services,budget,{},transporte=transport)
        t.usar("plan","planificar",{"institucion":"Nova"}, {},accept)
        t.usar("respuesta","redactar",{"E1":"Documento comprobado"}, {},accept)
        self.assertEqual(calls[-2][2],calls[-1][2])
        self.assertEqual(t.autores["respuesta"]["proveedor"],"ollama")

    def test_cuatro_llamadas(self):
        """Máximo cuatro llamadas, incluso con dos etapas y varios fallos."""
        def transport(s,messages,schema,phase,timeout):
            if phase=="plan" and s.nombre!="gemini": raise p.Fallo("tiempo")
            if phase=="respuesta": raise p.Fallo("conexion")
            return '{"ok":true}'
        services,budget=configs()
        t=p.Turno(services,budget,{},transporte=transport)
        self.assertTrue(t.usar("plan","s",{}, {},accept))
        self.assertIsNone(t.usar("respuesta","s",{}, {},accept))
        self.assertLessEqual(t.llamadas,4)

    def test_recuperacion(self):
        """La cuota abre solo el circuito afectado; un nuevo turno lo recupera tras Retry-After."""
        now=[0]; health={}; calls=[]
        def transport(s,*_):
            calls.append(s.nombre)
            if s.nombre=="groq" and len(calls)==1: raise p.Fallo("cuota",120)
            return '{"ok":true}'
        services,budget=configs()
        def run():
            t=p.Turno(services,budget,health,clock=lambda:now[0],transporte=transport)
            t.usar("plan","s",{}, {},accept); return t
        self.assertEqual(run().autores["plan"]["proveedor"],"ollama")
        now[0]=80;self.assertEqual(run().intentos[0]["estado"],"en_pausa")
        now[0]=121;self.assertEqual(run().autores["plan"]["proveedor"],"groq")
        self.assertFalse(health)

    def test_tiempo_pared(self):
        """Un transporte bloqueado no prolonga el presupuesto ni escribe en la sesión al terminar."""
        waiting=threading.Event()
        def stalled(*_):
            waiting.wait(2);return '{"ok":true}'
        services,_=configs("ollama");t=p.Turno(services,.35,{},transporte=stalled)
        start=time.monotonic()
        try:
            self.assertIsNone(t.usar("plan","s",{}, {},accept))
            self.assertLess(time.monotonic()-start,.8)
            self.assertEqual(t.intentos[0]["estado"],"tiempo")
            other=p.Turno(services,1,{},transporte=stalled)
            self.assertIsNone(other.usar("plan","s",{}, {},accept))
            self.assertEqual(other.intentos[0]["estado"],"ocupado")
        finally: waiting.set();time.sleep(.03)
        self.assertFalse(t.autores)

    def test_todo_caido(self):
        """Con un fallo de cada servicio, la capa de modelos cede a las reglas."""
        def down(*_): raise p.Fallo("conexion")
        services,b=configs(); t=p.Turno(services,b,{},transporte=down)
        self.assertIsNone(t.usar("plan","s",{}, {},accept))
        self.assertEqual(t.llamadas,3); self.assertEqual(t.resumen()["modo_respuesta"],"reglas")

    def test_ollama_loopback(self):
        """Una dirección externa, credenciales embebidas o un alias cloud se rechazan antes de abrir red."""
        for url in ["https://ejemplo.invalid","http://127.0.0.1@ejemplo.invalid","http://0.0.0.0:11434","http://127.0.0.1/x"]:
            with self.assertRaises(p.Fallo):p.direccion_local(url)
        self.assertEqual(p.direccion_local("http://[::1]:11434"),"http://[::1]:11434")
        with patch.object(p,"peticion") as net:
            with self.assertRaises(p.Fallo):p.ollama(p.Servicio("ollama","modelo:cloud",1),[],{},"plan",1)
            net.assert_not_called()

    def test_http_ollama(self):
        """HTTP real de loopback y servidor Ollama simulado: esquema, chat y respuesta sin razonamiento."""
        seen=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                seen.append((self.path,json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(200); self.end_headers()
                self.wfile.write(json.dumps({"done":True,"message":{"thinking":"interno-sintetico","content":'{"ok":true}'}}).encode())
        h=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        threading.Thread(target=h.serve_forever,daemon=True).start()
        try:
            s=p.Servicio("ollama","qwen3:4b",2,host="http://127.0.0.1:"+str(h.server_port))
            raw=p.ollama(s,[],n.PLAN,"plan",2)
            self.assertEqual(json.loads(raw),{"ok":True}); self.assertEqual(seen[0][0],"/api/chat")
            self.assertFalse(seen[0][1]["think"]);self.assertEqual(seen[0][1]["format"],n.PLAN)
        finally:h.shutdown();h.server_close()

    def test_wire_groq(self):
        """El adaptador Groq genera el esquema estricto y descarta reasoning."""
        with patch.object(p,"peticion",return_value={"choices":[{"message":{"content":"{}","reasoning":"privado"}}]}) as call:
            self.assertEqual(p.groq(configs()[0][0],[],n.PLAN,"plan",1),"{}")
            url,headers,body,timeout=call.call_args.args
            self.assertEqual(url,"https://api.groq.com/openai/v1/chat/completions")
            self.assertTrue(body["response_format"]["json_schema"]["strict"])
            self.assertNotIn("tools",body);self.assertIn("Authorization",headers)

    def test_wire_gemini(self):
        """Gemini usa el esquema JSON y filtra partes thought antes de validar."""
        with patch.object(p,"peticion",return_value={"candidates":[{"content":{"parts":[{"thought":True,"text":"privado"},{"text":"{}"}]}}]}) as call:
            self.assertEqual(p.gemini(configs()[0][-1],[{"content":"instruccion"},{"content":"mensaje"}],n.PLAN,"plan",1),"{}")
            url,headers,body,_=call.call_args.args
            self.assertEqual(body["generationConfig"]["responseJsonSchema"],n.PLAN)
            self.assertIn("x-goog-api-key",headers);self.assertNotIn("?",url)

    def test_codigos_http(self):
        """Errores HTTP 401, 403, 404, 408, 429, 503 y 500 tienen causas auditables."""
        from unittest.mock import MagicMock
        for code,why in {401:"credencial",403:"credencial",404:"modelo_ausente",408:"tiempo",429:"cuota",503:"saturacion",500:"servicio"}.items():
            conn=MagicMock();res=conn.getresponse.return_value;res.status=code;res.getheader.return_value="70"
            with patch("http.client.HTTPSConnection",return_value=conn):
                with self.assertRaises(p.Fallo) as e:p.peticion("https://ejemplo.invalid/api",{}, {},1)
                self.assertEqual(e.exception.motivo,why); self.assertEqual(e.exception.pausa,70)

    def test_sin_historial_ni_persona(self):
        """Minimiza el contexto, evita texto libre de turnos anteriores y reconoce identificadores sintéticos."""
        for s in ["mi nombre es Persona de Prueba","contacto alice@example.invalid","mi RUT es ficticio","mi teléfono es privado"]:
            self.assertTrue(n.privado(s))
        state={"context":{"goal":"social_connection","student_id":"SINTETICO"},"messages":[{"content":"privado"}],
               "interest":"dato privado","memoria":[["mostrar_ficha"]]*10}
        serialized=json.dumps(n.contexto(state))
        self.assertNotIn("privado",serialized);self.assertNotIn("SINTETICO",serialized)
        self.assertEqual(len(n.contexto(state)["ultimas_acciones"]),4)

    def test_inyeccion_en_contrato(self):
        """El plan rechaza herramientas ajenas, preguntas redundantes y argumentos sin cita del usuario."""
        mem={"invitacion":None,"disponibilidad":None,"institucion":"Nova","distrito":"Nébula"}
        for bad in [plan("ejecutar_codigo"),plan("guardar"),plan("aceptar"),plan("preguntar",ask="institution_id"),
                    plan("consultar_ficha",["telefono","telefono"]),plan("buscar_pares",interest="natación"),
                    plan("buscar_pares",franja="sábado"),plan("buscar_pares")|{"pensamiento":"texto"}]:
            self.assertIsNone(n.validar_plan(bad,"hola",mem))

    def test_ficciones(self):
        """Números, direcciones, registros, enlaces, cupos y eventos inventados activan rechazo semántico."""
        evidence={"campo_pregunta":"","obligatorias":["E1"],"evidencias_disponibles":{"E1":"Dato verificado."}}
        for opening in ["Ya tienes dos cupos","Te inscribí","Te entiendo. Hay becas","Llama al 555123456",
                        "Mira https://ejemplo.invalid","Se hará en Avenida del Sol","Vamos a la Fiesta Aurora"]:
            self.assertIsNone(n.ensamblar({"apertura":opening,"evidencias":["E1"],"pregunta":""},evidence))
        for ids in [[],["E2"],["E1","E1"]]:
            self.assertIsNone(n.ensamblar({"apertura":"","evidencias":ids,"pregunta":""},evidence))

    def test_apertura_y_pregunta(self):
        """Admite una pregunta inédita del campo correcto y rechaza pedir un dato diferente."""
        ev={"campo_pregunta":"district_id","obligatorias":[],"evidencias_disponibles":{}}
        good={"apertura":"Vamos a tu ritmo","evidencias":[],"pregunta":"¿Qué zona te acomoda para empezar?"}
        self.assertIn("zona te acomoda",n.ensamblar(good,ev)["texto"])
        self.assertIsNone(n.ensamblar({**good,"pregunta":"¿En qué universidad estudias?"},ev))

    def test_python(self):
        """El guardián acepta 3.12 y sale con instrucciones antes de importar Pandas en 3.14."""
        comprobar((3,12))
        with self.assertRaisesRegex(SystemExit,"3.12"):comprobar((3,14))

