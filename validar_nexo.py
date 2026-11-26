"""Ejecuta la auditoría reproducible. Nunca requiere claves o un servicio de IA."""
from entorno import comprobar
comprobar()
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parent
class Resultado(unittest.TextTestResult):
    def __init__(self,*a,**kw): super().__init__(*a,**kw);self.filas=[]
    def row(self,test,status,detail=""):
        self.filas.append({"id":test.id(),"caso":test.shortDescription() or test.id(),"resultado":status,"detalle":detail})
    def addSuccess(self,test): super().addSuccess(test);self.row(test,"OK")
    def addFailure(self,test,err): super().addFailure(test,err);self.row(test,"FALLO",str(err[1])[:400])
    def addError(self,test,err): super().addError(test,err);self.row(test,"ERROR",str(err[1])[:400])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida",type=Path,default=Path("resultados-locales"))
    args=parser.parse_args();out=args.salida.resolve();out.mkdir(exist_ok=True,parents=True);os.chdir(ROOT)
    os.environ.update(NEXO_MODO="reglas",GROQ_API_KEY="",GEMINI_API_KEY="")
    suite=unittest.defaultTestLoader.discover(str(ROOT/"pruebas"),pattern="test_*.py",top_level_dir=str(ROOT))
    r=unittest.TextTestRunner(verbosity=1,resultclass=Resultado).run(suite)
    (out/"arquitectura_interfaz.json").write_text(json.dumps(r.filas,ensure_ascii=False,indent=2),encoding="utf-8")
    codes=[not r.wasSuccessful()]
    for script,name in [("recorridos.py","recorridos"),("servidor.py","servidor")]:
        run=subprocess.run([sys.executable,str(ROOT/"pruebas"/script),str(out/(name+".json"))])
        codes.append(run.returncode)
    print("Resultados:",out)
    return int(any(codes))
if __name__=="__main__":sys.exit(main())

