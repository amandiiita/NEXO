# NEXO

**Agente inteligente para la integración universitaria en Ciudad Aethera.**

NEXO es una aplicación desarrollada con Streamlit que facilita el acceso a oportunidades de participación universitaria mediante el análisis contextual de calendarios institucionales y servicios de apoyo.

El sistema utiliza un agente basado en un modelo generativo para interpretar las solicitudes de los estudiantes, identificar la información relevante y orientar las respuestas a partir de los datos disponibles.

---

## Arquitectura

NEXO separa la interfaz de usuario, el procesamiento semántico y el acceso a los datos institucionales.

| Componente              | Tecnología       | Función                                           |
| ----------------------- | ---------------- | ------------------------------------------------- |
| Interfaz                | Streamlit        | Interacción y presentación de resultados          |
| Lógica de aplicación    | Python 3.10+     | Orquestación y reglas de decisión                 |
| Procesamiento semántico | Google GenAI SDK | Interpretación de intenciones y solicitudes       |
| Modelo generativo       | Gemini Flash     | Comprensión contextual y generación de respuestas |
| Datos tabulares         | Pandas           | Carga, transformación y consulta de datos         |

### Fuentes de datos

NEXO trabaja con los siguientes conjuntos del Data Pack de Ciudad Aethera:

* **D7 — Calendario institucional:** actividades y eventos registrados por la institución.
* **D6 — Mapa de servicios:** ubicación, horarios, canales y características de los servicios de apoyo.

Las recomendaciones dependen de la información disponible en estas fuentes y de las reglas de decisión implementadas en la aplicación.

---

## Diseño de interfaz

La interfaz utiliza una composición visual minimalista orientada a la legibilidad y la continuidad entre elementos.

* **Mesh gradient:** fondos con transiciones cromáticas suaves inspiradas en el efecto aurora.
* **Glassmorphism:** barra lateral con transparencia y tratamiento visual de cristal.
* **Diseño responsivo:** distribución adaptable a distintos tamaños de pantalla.
* **Jerarquía visual:** tipografía clara, espaciado consistente y separación entre contexto, interacción y resultados.

El diseño busca mantener la atención en las recomendaciones y en la información necesaria para comprenderlas.

---

## Seguridad y guardarraíles

NEXO incorpora mecanismos de clasificación de intenciones mediante instrucciones estructuradas (*prompt engineering*). El objetivo es identificar la finalidad de una solicitud a partir de su contexto, sin depender exclusivamente de listas rígidas de palabras clave.

### Clasificación de intenciones

| Intención           | Propósito                                                                   |
| ------------------- | --------------------------------------------------------------------------- |
| `social_connection` | Solicitudes relacionadas con actividades y oportunidades de conexión social |
| `greeting`          | Saludos e interacciones iniciales                                           |
| `human_support`     | Solicitudes que requieren orientación hacia apoyo humano                    |
| `out_of_context`    | Solicitudes fuera del alcance funcional de NEXO                             |

La clasificación permite orientar el flujo de interacción según la intención identificada. No sustituye la evaluación de seguridad ni garantiza por sí sola una clasificación correcta en todos los casos.

### Protección de credenciales

Las credenciales y claves de API deben mantenerse fuera del código fuente y del repositorio público.

Para la configuración local, NEXO utiliza los mecanismos de secretos de Streamlit. El archivo `.gitignore` debe excluir los archivos de configuración sensibles y otros artefactos locales.

Ejemplo de configuración:

```toml
# .streamlit/secrets.toml

GOOGLE_API_KEY = "YOUR_API_KEY"
```

Acceso desde Python:

```python
import streamlit as st

api_key = st.secrets["GOOGLE_API_KEY"]
```

No publiques claves reales ni archivos que contengan credenciales. Si una clave se expone accidentalmente, revócala y genera una nueva.

---

## Instalación local

### Requisitos

* Python 3.10 o superior.
* Una clave de API válida para el servicio de Google GenAI.
* Git.

### 1. Clonar el repositorio

```bash
git clone https://github.com/amandiiita/NEXO.git
cd NEXO
```

### 2. Crear un entorno virtual

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias

Si el repositorio incluye `requirements.txt`:

```bash
pip install -r requirements.txt
```

Asegúrate de que el archivo incluya todas las dependencias que utiliza la versión actual de la aplicación, incluido el SDK de Google GenAI si corresponde.

### 4. Configurar los secretos

Crea el directorio de configuración si todavía no existe:

```bash
mkdir -p .streamlit
```

Crea `.streamlit/secrets.toml` y añade tu clave de API:

```toml
GOOGLE_API_KEY = "YOUR_API_KEY"
```

No subas este archivo a GitHub.

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

Streamlit mostrará la dirección local desde la que podrás acceder a la aplicación.

---

## Estructura del proyecto

La estructura exacta depende de los archivos presentes en el repositorio. Una organización posible para los módulos descritos es:

```text
NEXO/
├── app.py
├── agent.py
├── tools.py
├── ranking.py
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml
```

* `app.py`: interfaz y flujo principal de la aplicación.
* `agent.py`: interpretación de solicitudes y coordinación del agente.
* `tools.py`: acceso y consulta de los datos.
* `ranking.py`: criterios de puntuación y priorización de resultados.
* `requirements.txt`: dependencias de Python.
* `.streamlit/secrets.toml`: configuración local de credenciales; no debe versionarse.

---

## Alcance

NEXO está diseñado para facilitar el descubrimiento de oportunidades de participación universitaria a partir de información institucional disponible.

El sistema no sustituye el acompañamiento profesional, no diagnostica condiciones de salud mental y no reemplaza los servicios de apoyo humano.

Su función es orientar al estudiante hacia oportunidades y recursos pertinentes dentro del contexto de Ciudad Aethera.

---

**NEXO**
*Tecnología para facilitar la conexión humana.*
