# 🔗 NEXO — Agente Logístico de Integración Universitaria (Ciudad Aethera)

Prototipo funcional desarrollado por **Batch S26** para el **Entregable 2 (Misión 4: Aislamiento Social)**. NEXO transforma información institucional dispersa del Data Pack (`D7`, `D6` y `D2`) en rutas accionables y explicables de participación estudiantil, priorizando a estudiantes con barreras de tiempo, trabajo y adaptación territorial.

---

## 🚀 Arquitectura del Proyecto

```text
NEXO/
├── app.py                  # Interfaz web conversacional y tarjetas explicables (Streamlit)
├── agent.py                # Intérprete agéntico (Gemini 2.5 Flash + respaldo semántico) y enrutador ético
├── ranking.py              # Motor determinista de puntaje de compatibilidad (0 a 100 puntos)
├── tools.py                # Herramientas de consulta y cruce de fechas sobre D7, D6 y D2
├── data_loader.py          # Ingesta y normalización multiplataforma de archivos CSV y GeoJSON
├── analisis data pack.R    # Diagnóstico estadístico en R sobre D1 y D3 (Línea base: 31,0%)
├── requirements.txt        # Dependencias del proyecto
└── data/
    ├── D2_support_services.csv
    ├── D6_services_map.geojson
    └── D7_calendar.csv
```

---

## ⚙️ Instalación y Ejecución (Windows, macOS y Linux)

### 1. Clonar o descargar el repositorio
```bash
git clone [https://github.com/amandiiita/NEXO.git](https://github.com/amandiiita/NEXO.git)
cd NEXO
```

### 2. Crear entorno virtual e instalar dependencias

**En macOS / Linux (Terminal):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**En Windows (PowerShell / CMD):**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar API Key de Gemini (Opcional)
El sistema incluye un motor semántico determinista de respaldo que permite ejecutar toda la demostración sin conexión a API externa. Para activar la capa generativa en vivo con **Gemini 2.5 Flash**, crea el archivo `.streamlit/secrets.toml` en la raíz del proyecto:

```toml
GEMINI_API_KEY = "TU_CLAVE_AQUI"
```

### 4. Ejecutar la aplicación web
```bash
streamlit run app.py
```
La aplicación se abrirá automáticamente en el navegador en `http://localhost:8501`.

---

## 📊 Conexión con el Data Pack (Misión 4)

1. **Fase Diagnóstica (`analisis data pack.R` sobre `D1` y `D3`):** Identifica el indicador de línea base (**31,0% de estudiantes sin red de apoyo**) y demuestra que el aislamiento se concentra en migrantes internos con baja participación (75,8%) y estudiantes que trabajan más de 20 horas semanales, fundamentando empíricamente los pesos del algoritmo de ranking.
2. **Fase Operativa (`app.py`, `agent.py`, `ranking.py`, `tools.py` sobre `D7`, `D6` y `D2`):** Cruza en tiempo real las restricciones declaradas por el estudiante con las actividades del calendario académico (`D7`), los espacios permanentes de apoyo entre pares y orientación georreferenciados (`D6`) y las tasas históricas de asistencia y tiempos de espera (`D2`).

---

## 🛡️ IA Responsable y Gobernanza de Datos

- **Privacidad desde el diseño y no perfilamiento:** `D1` y `D3` se utilizan exclusivamente a nivel estadístico agregado. El agente en vivo no consulta historiales clínicos ni académicos individuales para etiquetar al estudiante.
- **Explicabilidad (Cero Alucinación):** Todas las recomendaciones provienen de registros verificables del Data Pack e informan su puntaje de compatibilidad desglosado por criterio.
- **Cortafuegos ético de derivación humana:** Ante señales de malestar emocional o solicitud de ayuda profesional, NEXO detiene la recomendación recreativa, declara que no realiza diagnósticos clínicos y deriva inmediatamente a los canales oficiales de orientación (`counseling` y `peer_support` en `D6` + `D2`) del distrito correspondiente.
