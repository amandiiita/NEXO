"""Antes de importar Pandas o Streamlit, también desde los validadores."""
import sys

def comprobar(version=None):
    version = version if version is not None else sys.version_info[:2]
    if tuple(version[:2]) != (3, 12):
        raise SystemExit("NEXO necesita Python 3.12 para esta distribución. "
                         "En macOS crea el entorno con python3.12 -m venv .venv; "
                         "en Windows usa py -3.12 -m venv .venv. Consulta README.md.")

if __name__ == "__main__":
    comprobar()
    print("Entorno compatible con NEXO · Python 3.12")
