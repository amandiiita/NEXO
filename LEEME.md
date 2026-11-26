# Cómo descargar y abrir NEXO

Creamos NEXO para ayudar a estudiantes a encontrar actividades, espacios de encuentro y orientación universitaria en Ciudad Aethera. Te dejo los pasos para probar la demo en tu computador. La instalación se hace una sola vez.

## 1. Descarga el proyecto

Descarga [NEXO desde GitHub](https://github.com/amandiiita/NEXO/archive/refs/heads/main.zip). También puedes seleccionar **Code → Download ZIP** en el repositorio. En Mac puedes abrirlo con doble clic. En Windows, haz clic derecho y elige **Extraer todo**. En Linux, elige **Extraer aquí**.

Abre la carpeta extraída. Sabrás que estás en el lugar correcto cuando veas **iniciar.py**, **requirements.txt** y la carpeta **data** juntos. Los datos de la demo ya vienen incluidos.

## 2. Abre una terminal en esa carpeta

- **Mac:** abre Terminal, escribe `cd ` dejando un espacio al final, arrastra la carpeta de NEXO desde Finder a la ventana y presiona Enter.
- **Windows:** abre la carpeta en el Explorador de archivos. Escribe `powershell` en la barra donde aparece la ruta y presiona Enter.
- **Linux:** dentro de la carpeta, haz clic derecho en un espacio vacío y selecciona **Abrir en una terminal**, si tu escritorio ofrece esa opción. También puedes usar `cd` seguido de la ruta de la carpeta.

## 3. Instala lo necesario

NEXO usa **Python 3.12**. Elige **una** de las siguientes opciones. Ejecuta los comandos de tu opción en orden y espera a que termine cada uno.

### Si ya usas Conda en Mac, Windows o Linux

Si en tu terminal aparece `(base)`, probablemente ya tienes Conda. Esta opción instala la versión de Python que necesita NEXO dentro de su propio entorno. En Windows puedes usar Anaconda Prompt si PowerShell no reconoce `conda`. Recuerda entrar a la carpeta del proyecto en esa nueva ventana.

```sh
conda create -n nexo312 python=3.12 pip
conda activate nexo312
python -m pip install -r requirements.txt
```

Si Conda pregunta si quieres continuar, escribe **y** y presiona Enter. Si ya creaste el entorno `nexo312` en una instalación anterior, empieza en la segunda línea.

### Mac o Linux sin Conda

Comprueba la versión con `python3.12 --version`. Si el comando no existe, instala Python 3.12 antes de continuar. En Mac, si usas Homebrew, puedes ejecutar `brew install python@3.12`. En Linux usa el gestor de paquetes de tu distribución e incluye el componente `venv` para Python 3.12 si viene por separado.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Windows sin Conda

Comprueba la versión con `py -3.12 --version`. Si Windows no la encuentra, instala Python 3.12 de 64 bits con el lanzador de Python y vuelve a abrir PowerShell en la carpeta del proyecto. [Descargas oficiales de Python](https://www.python.org/downloads/windows/)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. Abre NEXO

En la misma terminal, ejecuta el comando que corresponde a la opción que elegiste.

| Cómo lo instalaste | Comando de inicio |
| --- | --- |
| Con Conda, en cualquier sistema | `python iniciar.py` |
| Mac o Linux con el entorno .venv | `.venv/bin/python iniciar.py` |
| Windows con el entorno .venv | `.\.venv\Scripts\python.exe iniciar.py` |

Se abrirá una pestaña en tu navegador. Si no se abre sola, entra a **[NEXO en tu computador](http://127.0.0.1:8503)**. Deja la terminal abierta mientras conversas. Puedes empezar escribiendo «Quiero conocer gente, pero trabajo hasta las seis» o probar uno de los tres botones de demostración.

## 5. Conecta la inteligencia artificial

Puedes abrir la demo y probar los recorridos guiados aunque todavía no tengas una clave. Para probar la conversación con un modelo, elige la opción que te acomode.

**Con Ollama en tu computador.** Instala [Ollama](https://ollama.com/download), abre la aplicación o inicia el servicio y ejecuta `ollama pull qwen3:4b` en otra terminal. La descarga se hace una sola vez. Si ya tienes el modelo, puedes comprobarlo con `ollama list`. Con Ollama activo y las claves de nube vacías, NEXO puede usar Qwen localmente.

**Con Groq o Gemini.** En la carpeta del proyecto encontrarás `.streamlit/secrets.toml.example`. En Mac puedes mostrar las carpetas ocultas con **Cmd + Shift + punto**, y en Linux con **Ctrl + H**. Duplica el archivo de ejemplo dentro de esa misma carpeta y llama a la copia **secrets.toml**. Si la copia ya existe, edítala directamente. Ábrela con un editor de texto y pega tu propia clave entre las comillas de `GROQ_API_KEY` o `GEMINI_API_KEY`. Guarda el archivo solo en tu equipo.

Con el modo predeterminado, NEXO intenta usar Groq, Ollama y Gemini, en ese orden, según lo que tengas configurado. Si quieres usar **solo Ollama**, cambia la línea del modo a `NEXO_MODO = "local"` en `secrets.toml`. Después de cambiar la configuración, detén la app con **Ctrl + C** en la terminal y vuelve a ejecutar el comando del paso 4. Envía un mensaje y abre **Detalles técnicos** en la barra lateral para ver quién respondió.

## Para volver a usarlo otro día

Abre una terminal en la carpeta de NEXO. Si usaste Conda, ejecuta primero `conda activate nexo312`. Si quieres usar Qwen, abre también Ollama. Luego repite únicamente el comando de inicio del paso 4.

Si aparece un error que dice que no encuentra **requirements.txt** o **iniciar.py**, vuelve al paso 2 y elige la carpeta donde realmente ves esos archivos. Si el puerto 8503 está ocupado, añade `--server.port 8504` al comando de inicio y abre [NEXO en el puerto 8504](http://127.0.0.1:8504).
