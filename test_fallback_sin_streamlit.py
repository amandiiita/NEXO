"""Entrada conservada para comprobar el respaldo sin importar Streamlit."""
from entorno import comprobar
comprobar()
import unittest
from pruebas.test_arquitectura import Arquitectura

if __name__ == "__main__":
    unittest.main(verbosity=2)

