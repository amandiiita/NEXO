"""Recorrido real HTTP y WebSocket de Streamlit, sin controlador de navegador."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import os
from urllib.request import urlopen
from websockets.sync.client import connect
from streamlit.proto.BackMsg_pb2 import BackMsg
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg

def smoke():
    root=Path(__file__).resolve().parents[1]
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        port=sock.getsockname()[1]
    url=f"http://127.0.0.1:{port}"
    env={**os.environ,"NEXO_MODO":"reglas","GROQ_API_KEY":"","GEMINI_API_KEY":""}
    server=subprocess.Popen([sys.executable,"-m","streamlit","run","app.py","--server.headless","true",
        "--server.address","127.0.0.1","--server.port",str(port),"--browser.gatherUsageStats","false"],
        env=env,cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    observed=[]
    try:
        for _ in range(70):
            try:
                with urlopen(url+"/_stcore/health",timeout=0.7) as f:
                    if f.read()==b"ok": break
            except OSError:
                time.sleep(.1)
        else: raise RuntimeError("El servidor no respondió a health")
        with connect(f"ws://127.0.0.1:{port}/_stcore/stream",subprotocols=["streamlit"],origin=url,
                     max_size=8*1024*1024,open_timeout=5) as ws:
            def rerun(action=None, value=None):
                back=BackMsg()
                client=back.rerun_script
                client.context_info.locale="es-CL"
                client.context_info.timezone="America/Santiago"
                client.context_info.url=url
                if action:
                    item=client.widget_states.widgets.add(id=action)
                    if value is None: item.trigger_value=True
                    else: item.chat_input_value.data=value
                ws.send(back.SerializeToString())
                text=[]; buttons={}; chat_id=None
                for _ in range(1500):
                    msg=ForwardMsg.FromString(ws.recv(timeout=9))
                    if msg.HasField("script_finished"): break
                    if not msg.HasField("delta") or not msg.delta.HasField("new_element"): continue
                    el=msg.delta.new_element
                    if el.HasField("exception"): raise AssertionError(el.exception.message)
                    if el.HasField("chat_input"): chat_id=el.chat_input.id
                    if el.HasField("button"): buttons[el.button.label]=el.button.id
                    if el.HasField("markdown"): text.append(el.markdown.body)
                if not chat_id: raise AssertionError("No se recibió el control de chat por WebSocket")
                return chat_id,buttons,"\n".join(text)
            chat,btn,body=rerun()
            assert {"Demo Conversacional","Demo Integración","Demo Derivación"} <= btn.keys()
            observed.append("Servidor en loopback, HTTP health y tres demostraciones")
            chat,btn,body=rerun(chat,"Me puedes ayudar con mi tarea de cálculo")
            assert "ejercicios académicos" in body
            observed.append("Mensaje escrito → límite académico")
            chat,btn,body=rerun(chat,"Sí")
            assert "¿Cuándo puedes participar?" in body
            observed.append("Afirmación → pregunta de disponibilidad")
            chat,btn,body=rerun(btn["Demo Integración"])
            assert "Espacio Lumen Pares" in body and "Cómo participar" in btn
            observed.append("Demo Integración → tarjeta de D6")
            chat,btn,body=rerun(btn["Cómo participar"])
            assert "Guardar próximo paso" in btn
            chat,btn,body=rerun(btn["Guardar próximo paso"])
            assert "Guardé tu próximo paso" in body
            observed.append("Participar → guardar → paso en barra lateral")
            chat,btn,body=rerun(btn["Demo Derivación"])
            assert "Orientación" in body
            observed.append("Demo Derivación → orientación humana")
            chat,btn,body=rerun(btn["Reiniciar conversación"])
            assert "Guardar próximo paso" not in btn and "Espacio Lumen Pares" not in body
            observed.append("Reinicio de sesión")
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except subprocess.TimeoutExpired: server.kill(); server.wait()
    return observed

if __name__=="__main__":
    rows=smoke()
    print("\n".join(rows))
    if len(sys.argv)>1: Path(sys.argv[1]).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")

