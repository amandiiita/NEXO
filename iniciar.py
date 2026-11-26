"""Punto de entrada privado. Comprueba Python antes de importar dependencias binarias."""
from entorno import comprobar

def main():
    comprobar()
    import os
    from pathlib import Path
    import sys
    from streamlit.web.cli import main as streamlit
    root = Path(__file__).resolve().parent
    os.chdir(root)
    sys.argv = ["streamlit", "run", str(root/"app.py"), "--server.address", "127.0.0.1", *sys.argv[1:]]
    return streamlit()

if __name__ == "__main__":
    raise SystemExit(main())

