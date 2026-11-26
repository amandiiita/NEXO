# Auditoría de NEXO · 26 de noviembre de 2026

**Resultado.** La aplicación adjunta, actualizada y ejecutada con Python 3.12.14, cumplió los 36 criterios de conversación. En la misma batería la versión anterior cumplió 21. Pasaron otras 52 pruebas de contratos, recuperación, datos e interfaz. Un servidor real de Streamlit completó la secuencia de siete verificaciones documentada abajo. Los tres adaptadores están implementados. Su calidad y latencia con modelos reales permanecen pendientes.

| Evidencia | Método | Resultado y alcance |
| --- | --- | --- |
| Comparación directa | Las mismas 36 secuencias contra las dos aplicaciones con modelos desactivados | 21/36 antes y 36/36 después. Los 15 casos corregidos y ambos textos observados están en `COMPARACION.csv` |
| Contratos y recuperación | 20 pruebas de transporte, validación, privacidad, presupuesto y circuitos | 20/20. Se simularon modelos, códigos HTTP, contenidos y esperas. Para Ollama se abrió una conexión HTTP real hacia un servidor de prueba en loopback |
| Recorridos adicionales y límites | 32 pruebas con Streamlit AppTest, catálogo adjunto real y modelos simulados o reglas | 32/32. Incluyen planificación, redacción, cambio de proveedor, contexto largo, datos ausentes, derivación, reinicio y guardado |
| Servidor real | Arranque en loopback, petición de salud HTTP, intercambio de mensajes y eventos de widgets mediante WebSocket | 7/7 hitos. Chat → límite académico → aceptación → demo de integración → participación y guardado → derivación → reinicio |
| Compatibilidad | Entorno aislado Linux CPython 3.12.14 con 35 distribuciones de ejecución, sin herencia de paquetes del sistema ni SDK de IA | Suite ejecutada con las versiones fijadas. Comprobaciones de requisitos sin conflictos. Se reutilizaron distribuciones instaladas. No se realizó una descarga limpia de dependencias en macOS ni Windows |
| Groq, Ollama y Gemini reales | Validador de tres turnos por proveedor, disponible en la entrega | **Pendiente.** En el entorno no había un daemon Ollama con Qwen3 ni credenciales independientes de prueba. Ninguna comprobación utilizó la credencial de la copia original |

## Qué cambió en la conversación

- «Me puedes ayudar con mi tarea de cálculo» antes terminaba en una pregunta genérica. Ahora explica el alcance académico, ofrece buscar actividades y entiende el «sí» del turno siguiente.
- «Me gustaría sentirme parte de este lugar nuevo» y «No cacho a nadie en la U» ahora inician una búsqueda de integración sin exigir que la persona diga «actividad» o «espacio».
- «¿Cuál es el teléfono y cuántos cupos quedan?» antes contestaba solo por el teléfono. Ahora identifica ambos datos faltantes y propone consultar a la institución. La capacidad nominal de D6 nunca se presenta como disponibilidad en vivo.
- Si la persona trabaja o «chambea» hasta las 18, se solicita su disponibilidad efectiva. Una corrección a «solo los sábados» conserva distrito e institución.
- D7 se consulta por objetivo. Una actividad fuera del distrito, de otra institución, vencida o sin coincidencia de interés queda fuera de las recomendaciones compatibles. El botón **Ver calendario ampliado** permite explorar explícitamente opciones más amplias.

## Control de regresiones

El respaldo pasó su propia suite original de 52 escenarios AppTest y sus 28 pruebas históricas de respaldo. Se aplicaron también 40 verificaciones históricas de funcionamiento a la nueva aplicación, sin retocar sus aserciones. **33 conservaron el resultado anterior y siete cambiaron deliberadamente.** Los resultados de ese control adicional están en `evidencia/regresiones_originales.json`.

| Nº histórico | Qué esperaba el test anterior | Cambio observable |
| --- | --- | --- |
| 23 | Mostrar Brújula como segunda opción tras buscar en Nébula | Se respeta el distrito indicado. Para salir de él se cambia la búsqueda |
| 28 | Afirmar que se revisaron otros distritos al buscar el domingo | La respuesta se limita al distrito consultado |
| 29, 30, 31 y 34 | Mostrar inmediatamente fechas, bienestar en otro distrito o actividades generales | Se pide ampliar el calendario cuando no hay coincidencias. El filtro de bienestar sí devuelve la actividad vigente al buscar en Gaia |
| 36 | Pasar directamente al distrito al salir del trabajo después de las 18 | La demo demuestra la confirmación de disponibilidad. El recorrido actualizado completa todas sus etapas hasta guardar |

Las pruebas del SDK anterior de Gemini siguen en la fuente de respaldo. La versión actual tiene pruebas específicas para el contrato de cada adaptador. La aprobación de una simulación indica que la lógica reacciona al estímulo suministrado. La calidad del modelo en preguntas libres debe medirse con una cuenta real.

## Integridad y seguridad

El origen fue el ZIP local adjunto. Se conservó una copia íntegra, anterior a la edición, con SHA-256 `4428b64e163179920087fe2d1784bb61d8d0c08267e44fe7c1bf7a25da0b5963`. El respaldo restaurable que se entrega incluye la fuente y los datos depurados de entornos virtuales, cachés y configuración privada.

Los tres archivos de datos coinciden byte a byte con el adjunto. Se verificaron 9.400 filas de D2, 15 servicios de D6 y 32 filas de D7. La fuente local D6 difiere en la serialización del GeoJSON respecto de GitHub, con igual contenido JSON. Se preservó la versión local. Se cotejaron el estilo, la cabecera visual y las tres funciones de renderizado de la conversación con el original. Las huellas constan en `evidencia/integridad.json`.

El ZIP original incluía una credencial configurada. Una clave de Groq también se había escrito en el chat. **Revoca esas credenciales y configura reemplazos en tu Mac.** La revisión de GitHub cubrió los diez commits alcanzables y 34 objetos de archivo del historial hasta `baa2862`. El cotejo no encontró la clave del adjunto, firmas de claves Groq/Google ni rutas de secretos en esos commits. El alcance de esa conclusión es ese historial. La entrega se hizo de forma privada.

## Qué falta medir antes de la final

1. **Credenciales y acceso real.** Ejecuta `validar_proveedor.py --proveedor groq` y el equivalente para Gemini con tus reemplazos. Cada prueba debe mostrar tres líneas **OK**. El validador da un resultado fallido si responde otro motor.
2. **Ollama en el M4.** Abre Ollama, verifica `ollama list`, precarga `qwen3:4b` y ejecuta `validar_proveedor.py --proveedor ollama`. Repite con el Wi-Fi apagado y registra tiempos en frío y en caliente. Ajusta el timeout local solo si tus mediciones lo requieren.
3. **Lenguaje regional.** Se usaron frases sintéticas de Chile y Perú y un doble de modelo. No hay una tasa de acierto general para lenguaje libre ni un benchmark comparativo realizado con las APIs reales. La redacción acotada puede descartar respuestas correctas que usen vocabulario imprevisto.
4. **Interfaz en el equipo del jurado.** Se probaron controles, estados y servidor. No se realizó una comparación visual de píxeles en navegador gráfico, porque el ejecutable Chromium no estaba instalado en este entorno. Revisa el tamaño de las tarjetas en la pantalla de presentación.
5. **Alcance de los datos.** La demo usa una fecha fija, intereses documentados en títulos y preferencias horarias expresables en una franja por conjunto de días. Para horarios complejos conviene confirmar una franja cada vez. D6 describe el programa, sin inscripción real, teléfono de atención ni cupos en vivo. Las pruebas usan recursos ficticios.
6. **Carga concurrente.** Se probó la ocupación del proveedor y el aislamiento de sesiones. El comportamiento bajo carga de un evento con muchas personas, las cuotas reales y el arranque nativo Windows/macOS siguen sin medirse.

## Repetir y revisar

`python validar_nexo.py` ejecuta las 52 pruebas, los 36 recorridos y el servidor. Usa el intérprete 3.12 del entorno del proyecto como muestran las instrucciones del README. Los resultados nuevos se guardan en `resultados-locales/`. Abre `MATRIZ_PRUEBAS.csv` para consultar el tipo, resultado y origen de cada verificación. `COMPARACION.csv` contiene los dos resultados por entrada. Los comprobantes originales están en `evidencia/`.

