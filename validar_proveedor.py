"""Prueba aislada con el modelo REAL configurado, sin aceptar respaldo como éxito."""
from entorno import comprobar
comprobar()
import argparse
import json
import os
from pathlib import Path
import sys
from pruebas.chat import Chat

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proveedor",choices=("groq","ollama","gemini"),required=True)
    parser.add_argument("--salida",type=Path,help="Guarda solo la traza de los turnos sintéticos")
    args=parser.parse_args()
    dest=args.salida.resolve() if args.salida else None
    os.chdir(Path(__file__).resolve().parent)
    os.environ["NEXO_MODO"]="local" if args.proveedor=="ollama" else "auto"
    os.environ["NEXO_PROVEEDORES"]=args.proveedor
    turns=[("Me gustaría sentirme parte de este lugar nuevo",lambda s: s["waiting"] in ("availability","district_id","institution_id")),
           ("Estudio en Nova Aether, me muevo por Nébula y quiero conocer gente después de las 18:00",
            lambda s:(s["messages"][-1].get("card") or {}).get("title")=="Espacio Lumen Pares"),
           ("¿Cuál es el teléfono y cuántos cupos quedan?",lambda s:all(x in s["messages"][-1]["content"] for x in ("número oficial","cupos")))]
    c=Chat(timeout=120);evidence=[];ok=True
    for question,criterion in turns:
        c.say(question)
        trace=c.state["traza"]; authors=trace["fases"]
        passed=bool(criterion(c.state)) and all(authors.get(k,{}).get("proveedor")==args.proveedor for k in ("plan","respuesta"))
        evidence.append({"consulta_sintetica":question,"aprobada":passed,"traza":trace})
        print(("OK" if passed else "SIN VALIDAR"),"·",args.proveedor,"·",trace["duracion_ms"],"ms ·",
              ", ".join(x["fase"]+"/"+x["estado"] for x in trace["intentos"]) or "sin llamadas")
        if not passed: ok=False;break
    if dest: dest.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    return 0 if ok else 1

if __name__=="__main__":sys.exit(main())

