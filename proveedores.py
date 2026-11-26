"""Transporte, selección y recuperación. No persiste textos, respuestas crudas ni credenciales."""
from concurrent.futures import Future, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
import http.client
import ipaddress
import json
import math
import re
import socket
import threading
import time
from urllib.parse import urlsplit


class Fallo(Exception):
    def __init__(self, motivo, pausa=0):
        super().__init__(motivo)
        self.motivo = motivo
        self.pausa = pausa


def modelo_seguro(value):
    return bool(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,88}", value or "")
                and ".." not in value and "//" not in value
                and not re.search(r"AIza|gsk_|sk-|token|secret", value, re.I))


def direccion_local(value):
    """Nunca usa proxies, DNS de terceros, redirecciones ni modelos Ollama Cloud."""
    try:
        url = urlsplit(value if "://" in value else "http://" + value)
        host = url.hostname or ""
        if host == "localhost":
            host = "127.0.0.1"
        if (not ipaddress.ip_address(host).is_loopback or url.scheme != "http"
                or url.username or url.password or url.query or url.fragment or url.path not in ("", "/")):
            raise ValueError()
        port = url.port or 11434
        return f"http://[{host}]:{port}" if ":" in host else f"http://{host}:{port}"
    except (TypeError, ValueError):
        raise Fallo("configuracion") from None


def seconds(value, default, low, high):
    try:
        number = float(value)
        return min(high, max(low, number)) if math.isfinite(number) else default
    except (ValueError, TypeError):
        return default


@dataclass(frozen=True)
class Servicio:
    nombre: str
    modelo: str
    timeout: float
    clave: str = field(default="", repr=False)
    host: str = ""
    error: str = ""


def peticion(url, headers, body, timeout):
    url = urlsplit(url)
    connection = (http.client.HTTPSConnection if url.scheme == "https" else http.client.HTTPConnection)(
        url.hostname, url.port, timeout=timeout)
    try:
        connection.request("POST", url.path, json.dumps(body, ensure_ascii=False).encode(),
                           {"Content-Type": "application/json", **headers})
        response = connection.getresponse()
        status = response.status
        if status != 200:
            retry = response.getheader("Retry-After", "")
            if retry and not retry.isdigit():
                try:
                    retry = parsedate_to_datetime(retry).timestamp() - time.time()
                except (ValueError, TypeError, OverflowError):
                    retry = 0
            reason = {400: "solicitud_rechazada", 401: "credencial", 403: "credencial",
                      404: "modelo_ausente", 408: "tiempo", 429: "cuota", 503: "saturacion"}.get(status, "servicio")
            raise Fallo(reason, seconds(retry, 0, 0, 900))
        data = response.read(65537)
        if len(data) > 65536:
            raise Fallo("formato")
        return json.loads(data)
    except (TimeoutError, socket.timeout):
        raise Fallo("tiempo") from None
    except (OSError, http.client.HTTPException):
        raise Fallo("conexion") from None
    except (ValueError, UnicodeError):
        raise Fallo("formato") from None
    finally:
        connection.close()


def groq(service, messages, schema, phase, timeout):
    body = {"model": service.modelo, "messages": messages, "temperature": 0.2,
            "max_completion_tokens": 1200, "response_format": {"type": "json_schema", "json_schema": {
                "name": phase, "strict": True, "schema": schema}}}
    if service.modelo.startswith("openai/gpt-oss"):
        body["reasoning_effort"] = "low"
    data = peticion("https://api.groq.com/openai/v1/chat/completions",
                    {"Authorization": "Bearer " + service.clave}, body, timeout)
    return data["choices"][0]["message"]["content"]


def ollama(service, messages, schema, phase, timeout):
    # Etiquetas cloud y URLs se rechazan antes de construir el cliente.
    if "cloud" in service.modelo.lower() or "/" in service.modelo and "." in service.modelo.split("/")[0]:
        raise Fallo("configuracion")
    data = peticion(direccion_local(service.host) + "/api/chat", {}, {
        "model": service.modelo, "messages": messages, "format": schema, "stream": False,
        "think": False, "keep_alive": "10m", "options": {"temperature": 0.15, "num_ctx": 8192, "num_predict": 520}
    }, timeout)
    if data.get("done") is False or data.get("done_reason") == "length":
        raise Fallo("formato")
    return data["message"]["content"]


def gemini(service, messages, schema, phase, timeout):
    if "/" in service.modelo:
        raise Fallo("configuracion")
    config = {"responseMimeType": "application/json", "responseJsonSchema": schema, "maxOutputTokens": 1400}
    if service.modelo.startswith("gemini-3"):
        config["thinkingConfig"] = {"thinkingLevel": "LOW"}
    data = peticion("https://generativelanguage.googleapis.com/v1beta/models/" + service.modelo + ":generateContent",
                    {"x-goog-api-key": service.clave}, {
        "systemInstruction": {"parts": [{"text": messages[0]["content"]}]},
        "contents": [{"role": "user", "parts": [{"text": messages[1]["content"]}]}],
        "generationConfig": config}, timeout)
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


# Un adaptador toma mensajes y un contrato; el resto de la app nunca importa un cliente.
REGISTRO = {
    "groq": (groq, "openai/gpt-oss-120b", "GROQ_API_KEY", 6),
    "ollama": (ollama, "qwen3:4b", "", 18),
    "gemini": (gemini, "gemini-3.8-flash", "GEMINI_API_KEY", 8),
}
CUPOS = {name: threading.BoundedSemaphore(2 if name != "ollama" else 1) for name in REGISTRO}
ESPERA = {"credencial": 300, "configuracion": 300, "modelo_ausente": 180, "cuota": 60,
          "saturacion": 20, "tiempo": 12, "conexion": 15, "ocupado": 1,
          "restricciones": 5, "formato": 5, "solicitud_rechazada": 60, "servicio": 20}

MOTIVOS = {"sin_clave":"sin credencial configurada", "credencial":"la credencial fue rechazada",
           "saturacion":"servicio saturado", "cuota":"límite de solicitudes", "tiempo":"se agotó el tiempo",
           "conexion":"no respondió la conexión", "ocupado":"hay otra solicitud en curso",
           "formato":"salida incompleta o ilegible", "restricciones":"salida incompatible con la evidencia o el contrato",
           "configuracion":"configuración inválida", "modelo_ausente":"modelo no disponible",
           "solicitud_rechazada":"el proveedor rechazó la solicitud", "presupuesto":"límite de tiempo o llamadas",
           "en_pausa":"en espera de recuperación", "servicio":"servicio no disponible"}


def configuracion(get):
    modo = get("NEXO_MODO", "auto").lower()
    orden = get("NEXO_PROVEEDORES", "groq,ollama,gemini")
    nombres = ["ollama"] if modo == "local" else list(dict.fromkeys(x.strip().lower() for x in orden.split(",")))
    if modo not in ("local", "auto"):
        nombres = []  # reglas explícitas o ajuste desconocido: cierre local seguro.
    servicios = []
    for nombre in nombres:
        if nombre not in REGISTRO:
            continue
        _, default, keyname, wait = REGISTRO[nombre]
        model = get("NEXO_" + nombre.upper() + "_MODEL", default)
        key = get(keyname, "") if keyname else ""
        host = get("OLLAMA_HOST", "http://127.0.0.1:11434") if nombre == "ollama" else ""
        error = "" if modelo_seguro(model) else "configuracion"
        if keyname and not key:
            error = "sin_clave"
        timeout = seconds(get("NEXO_" + nombre.upper() + "_TIMEOUT", ""), wait, 0.5, 90)
        servicios.append(Servicio(nombre, model if modelo_seguro(model) else "sin-modelo", timeout, key, host, error))
    presupuesto = seconds(get("NEXO_TURNO_TIMEOUT", ""), 36, 1, 100)
    return servicios, presupuesto


def limitada(servicio, fn, args, timeout):
    # Un trabajador tardío solo puede completar este Future; jamás toca sesión ni UI.
    cupo = CUPOS[servicio.nombre]
    if not cupo.acquire(blocking=False):
        raise Fallo("ocupado")
    result = Future()

    def run():
        try:
            result.set_result(fn(servicio, *args, timeout))
        except Exception as error:
            result.set_exception(error)
        finally:
            cupo.release()

    worker = threading.Thread(target=run, name="nexo-" + servicio.nombre, daemon=True)
    try:
        worker.start()
    except RuntimeError:
        cupo.release()
        raise Fallo("ocupado") from None
    try:
        return result.result(timeout=timeout)
    except FutureTimeout:
        raise Fallo("tiempo") from None


class Turno:
    """Un solo propietario del turno y del presupuesto. Los circuitos viven entre turnos."""
    def __init__(self, servicios, presupuesto, circuitos, *, clock=time.monotonic, transporte=None):
        self.servicios = servicios
        self.clock = clock
        self.inicio = clock()
        self.fin = self.inicio + presupuesto
        self.circuitos = circuitos
        self.transporte = transporte
        self.intentos = []
        self.autores = {}
        self.llamadas = 0
        self.herramientas = []
        self.fuentes = []
        self.privado = False
        self.local = ""
        self.fallidos = set()

    def registro(self, fase, s, estado, ms=0):
        self.intentos.append({"fase": fase, "proveedor": s.nombre, "modelo": s.modelo, "estado": estado, "ms": ms})

    def usar(self, fase, sistema, entrada, schema, validar):
        if self.local:
            return None
        servicios = [s for s in self.servicios if not self.privado or s.nombre == "ollama"]
        if fase == "respuesta" and self.autores.get("plan"):
            primero = self.autores["plan"]["proveedor"]
            servicios.sort(key=lambda s: s.nombre != primero)
        messages = [{"role": "system", "content": sistema},
                    {"role": "user", "content": json.dumps(entrada, ensure_ascii=False, separators=(",", ":"))}]
        for i, s in enumerate(servicios):
            key = (s.nombre, s.modelo)
            start = self.clock()
            if s.error:
                self.registro(fase, s, s.error)
                continue
            if key in self.fallidos or self.circuitos.get(key, 0) > start:
                self.registro(fase, s, "en_pausa")
                continue
            restantes = sum(not x.error and (x.nombre, x.modelo) not in self.fallidos
                            and self.circuitos.get((x.nombre, x.modelo), 0) <= start for x in servicios[i+1:])
            disponible = self.fin - start
            if self.llamadas >= 4 or disponible < 0.15:
                self.registro(fase, s, "presupuesto")
                break
            reserva = min(disponible * 0.45, 2.5 * restantes + (2.5 if fase == "plan" else 0))
            timeout = min(s.timeout, disponible - reserva)
            self.llamadas += 1
            try:
                adapter = self.transporte or REGISTRO[s.nombre][0]
                raw = limitada(s, adapter, (messages, schema, fase), timeout)
                if not isinstance(raw, str) or len(raw) > 10000:
                    raise Fallo("formato")
                parsed = json.loads(raw)
                value = validar(parsed)
                if value is None:
                    raise Fallo("restricciones")
            except Fallo as exc:
                reason, pause = exc.motivo, exc.pausa
            except (KeyError, IndexError, TypeError, ValueError, AttributeError):
                reason, pause = "formato", 0
            except Exception:
                reason, pause = "servicio", 0
            else:
                self.circuitos.pop(key, None)
                self.registro(fase, s, "aceptado", round((self.clock()-start)*1000))
                self.autores[fase] = {"proveedor": s.nombre, "modelo": s.modelo}
                return value
            self.registro(fase, s, reason, round((self.clock()-start)*1000))
            self.fallidos.add(key)
            self.circuitos[key] = self.clock() + max(ESPERA.get(reason, 15), pause)
        return None

    def herramienta(self, nombre, *fuentes):
        if nombre not in self.herramientas:
            self.herramientas.append(nombre)
        for source in fuentes:
            if source not in self.fuentes:
                self.fuentes.append(source)

    def resumen(self):
        fallos = [r for r in self.intentos if r["estado"] != "aceptado"]
        return {"modo_respuesta": "IA con evidencia" if "respuesta" in self.autores else "reglas",
                "fases": self.autores, "intentos": self.intentos, "herramientas": self.herramientas,
                "fuentes": self.fuentes, "duracion_ms": round((self.clock()-self.inicio)*1000),
                "respaldo": bool(fallos), "llamadas": self.llamadas, "ruta_local": self.local or
                ("privacidad" if self.privado else "")}

