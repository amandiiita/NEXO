# 🔗 NEXO — Agente Logístico de Integración Universitaria (Ciudad Aethera)

Prototipo funcional desarrollado por **Batch S26** para el **Entregable 2 (Misión 4: Aislamiento Social)**. NEXO transforma información institucional dispersa del Data Pack (`D7`, `D6` y `D2`) en rutas accionables y explicables de participación estudiantil, priorizando a estudiantes con barreras de tiempo, trabajo y adaptación territorial.

## 🚀 Arquitectura del Prototipo

- `app.py`: Interfaz web conversacional y tarjetas explicables en Streamlit.
- `agent.py`: Intérprete agéntico (Gemini 2.5 Flash + respaldo semántico) y enrutador ético.
- `ranking.py`: Motor determinista de puntaje de compatibilidad (0 a 100 puntos).
- `tools.py`: Herramientas de consulta y cruce de fechas sobre `D7`, `D6` y `D2`.
- `data_loader.py`: Ingesta y normalización de archivos CSV y GeoJSON.
- **Datasets integrados:** `D7_calendar.csv`, `D6_services_map.geojson` y `D2_support_services.csv`.

## ⚙️ Instalación y Ejecución

```bash
pip install -r requirements.txt
streamlit run app.py
