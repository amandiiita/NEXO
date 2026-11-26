# Cómo responde NEXO

## Un turno visto desde el chat

Si un estudiante escribe «¿Cuál es el teléfono y cuántos cupos quedan?», el plan puede pedir dos campos de la ficha que está consultando. NEXO identifica el servicio en D6 y construye dos afirmaciones independientes. En el catálogo adjunto figura un canal telefónico y una capacidad nominal. Faltan el número de atención y la ocupación actual. El redactor puede priorizar los cupos o el contacto y cerrar con la consulta que conviene hacer a la institución. La tarjeta, el paso a guardar y los hechos proceden de la aplicación.

| Etapa | Qué decide | Qué controla el código |
| --- | --- | --- |
| Entrada y memoria | El estudiante escribe libremente o usa un botón | Preferencias confirmadas, referente de la ficha, pregunta pendiente y últimas cuatro acciones. Controles locales de privacidad y seguridad |
| Plan estructurado | El modelo elige una herramienta, qué campos pedir y qué preferencia necesita aclarar | Herramienta autorizada, argumento admisible, citas literales del turno, confirmación antes de inferir disponibilidad a partir del trabajo |
| Ejecución local | La herramienta elegida busca pares, actividades, una ficha, una explicación u orientación sobre participación | Consulta y ordenación de D2/D6/D7, filtros, fecha del escenario y acceso a los datos. Una selección por botón ejecuta su acción directamente |
| Redacción fundamentada | El modelo recibe los resultados, escoge un motivo útil, ordena datos y formula acompañamiento o preguntas dentro del ámbito | Los hechos y advertencias obligatorios se ensamblan desde referencias válidas. Una pregunta de seguimiento debe corresponder a una acción disponible. El código construye las tarjetas y realiza el guardado |
| Entrega al chat | Un único mensaje por turno | Los fallos de redacción nunca vuelven a ejecutar la búsqueda o el guardado. Los fallos de la herramienta permiten recuperar la sesión y reintentar |

El plan puede, por ejemplo, preguntar primero por el distrito cuando el estudiante quiere empezar por un lugar cercano, reconocer que «encontrar mi grupo» pide espacios de pares o consultar varios campos de otra ficha mencionada por nombre. El contexto persiste por sesión. Una corrección de distrito, institución u horario invalida la búsqueda anterior. Los relatos personales y el historial completo del chat se quedan fuera de la memoria que reciben los proveedores.

## Elección de proveedores

| Proveedor | Elección para esta entrega | Cuándo conviene |
| --- | --- | --- |
| Groq | `openai/gpt-oss-120b`. El catálogo publica 500 tokens/s y USD 0,15/0,60 por millón de tokens de entrada/salida | Primera opción para planificar y redactar con esquema estricto. Se priorizó la capacidad de seguimiento de instrucciones. La adecuación al español chileno y peruano requiere contrastarse con el modelo real |
| Groq, alternativa | `openai/gpt-oss-20b`. El catálogo publica 1.000 tokens/s y USD 0,075/0,30 por millón de entrada/salida | Para comparar rapidez, adherencia al contrato y coste con el mismo validador. Ambos admiten el formato estricto utilizado por NEXO |
| Ollama | `qwen3:4b`. Artefacto local de unos 2,5 GB, ya descargado por el equipo | Segundo por independencia de internet. `think=false`, contexto de 8.192 tokens y retención solicitada de 10 minutos. El arranque en frío y la memoria efectiva deben medirse en el M4 |
| Gemini | `gemini-3.8-flash`, configurable. Llamada REST `generateContent` con esquema de salida | Tercera ruta para aprovechar la cuenta existente. Puede adelantarse en un equipo sin Ollama |
| Reglas locales | Motor conversacional de emergencia y recorridos guiados | Toman el turno cuando se agotan los proveedores. También ejecutan directamente la ruta sensible |

Las velocidades publicadas describen la generación en el servicio. El tiempo del turno también incluye conexión, espera, validación y, normalmente, dos generaciones. Las cuotas dependen de la cuenta. Se eligió Groq por la combinación de modelos de producción y esquema estricto, con Qwen3 en el Mac como segunda ruta para que una caída de internet deje un modelo disponible. El orden se cambia en configuración. No se entrenaron modelos. [Catálogo de Groq](https://console.groq.com/docs/models) · [Salidas estructuradas de Groq](https://console.groq.com/docs/structured-outputs) · [Cuotas](https://console.groq.com/docs/rate-limits)

La llamada estructurada de Groq propone una herramienta en JSON y Python la ejecuta localmente. Esta separación permite reutilizar el mismo contrato con Ollama y Gemini. Se descarta cualquier bloque de razonamiento del proveedor. Se usan solo el objeto final y las comprobaciones del agente. [API de Ollama](https://docs.ollama.com/api/chat) · [Salida estructurada en Ollama](https://docs.ollama.com/capabilities/structured-outputs) · [Modelo local](https://ollama.com/library/qwen3:4b) · [Gemini Flash](https://aistudio.google.com/docs/models/gemini-3.8-flash) · [Salida estructurada de Gemini](https://ai.google.dev/gemini-api/docs/structured-output)

## Presupuesto y recuperación

- Un turno de texto admite hasta **dos fases de IA y cuatro solicitudes en total**. El botón usa como máximo la fase de redacción. Se ejecuta una sola ruta de herramientas, que puede consultar varias tablas o campos.
- Los máximos iniciales son **6 s en Groq, 18 s en Ollama y 8 s en Gemini**, con **36 s compartidos**. El orquestador reserva parte del tiempo restante para la siguiente alternativa. Son parámetros iniciales sujetos a medición, especialmente en el M4. La lectura local de datos y el renderizado pueden sumar tiempo fuera del presupuesto de red.
- El circuito es independiente por proveedor y modelo dentro de la sesión y sobrevive a «Reiniciar conversación». Una credencial rechazada abre una pausa de 300 s, un modelo ausente de 180 s, una cuota de al menos 60 s y un timeout de 12 s. Un `Retry-After` válido puede ampliar la pausa hasta 900 s. El siguiente turno posterior al vencimiento vuelve a probar el servicio. Un rechazo de formato o del contrato también provoca cambio.
- Los trabajadores de red no tienen acceso al estado del chat. Hay un cupo concurrente para Ollama y dos por proveedor de nube en el proceso. Un intento tardío ocupa únicamente su cupo hasta que termina. Una respuesta que llegue tarde se descarta. Las facturas o el cómputo de un servicio remoto pueden continuar después de que el cliente deje de esperar.
- Si falla la última redacción tras un plan válido, se conserva la herramienta ejecutada y se muestra el texto local de esa ficha. La traza identifica por separado quién planificó y cómo se obtuvo la respuesta final.

## Evidencia, privacidad y seguridad

D6 aporta horarios y canales publicados. D2 aporta un promedio histórico por servicio. D7 aporta fechas, distrito y organizador. El motor separa una capacidad nominal de los cupos actualmente disponibles y una fecha de la hora exacta. La búsqueda de pares comprueba cruce de días y horario en el distrito elegido. Las actividades vigentes deben coincidir con distrito, institución o acceso interuniversitario, días e interés indicado según corresponda. Las actividades del calendario ampliado llevan un aviso explícito. Una coincidencia de interés exige evidencia en el título en este catálogo.

La redacción tiene libertad en el orden de los hechos, el motivo opcional, el acompañamiento y las preguntas. Los datos institucionales se representan en afirmaciones completas que el modelo referencia. Las partes generadas se validan con un vocabulario de conversación y con el campo o acción correspondiente. Esto evita que una dirección, una inscripción o una actividad inventada se cuele entre hechos verificados. También puede rechazar una frase española perfectamente válida. En ese caso se intenta otro redactor y queda constancia del rechazo.

Las señales sensibles reconocidas, el peligro inmediato y los turnos de una derivación activa usan la ruta local. Los identificadores reconocibles, como correos, teléfonos y claves, restringen el turno a Ollama o a reglas. Las llamadas de nube reciben la consulta minimizada, categorías del perfil y hechos recuperados, sin filas individuales de D2. La detección de identificadores en lenguaje libre tiene límites. Para una garantía operativa de mantener la consulta en el equipo, elige **modo local**, el modelo descargado y la configuración sin funciones de nube de Ollama. [Configuración local de Ollama](https://docs.ollama.com/faq)

La traza conserva fase, proveedor, modelo configurado, tiempos, estados, herramientas y los identificadores institucionales que se mostraron. El protocolo de apoyo distingue soledad social, solicitud de orientación y peligro inmediato. En el último caso deriva a emergencias reales del lugar y a una persona de confianza. La demo indica que Aethera es ficticia.

## Dónde hacer futuros cambios

| Archivo | Responsabilidad |
| --- | --- |
| `proveedores.py` | Registro de adaptadores, HTTPS/loopback, clasificación de errores, circuitos y presupuesto |
| `nexo_model.py` | Contrato del plan, instrucciones, minimización de memoria y validador de la respuesta |
| `agent.py`, `tools.py` y `ranking.py` | Consultas institucionales y priorización |
| `app.py` | Estado conversacional, ejecución de las herramientas, seguridad local, tarjetas y traza |
| `data_loader.py` y `entorno.py` | Integridad del catálogo y comprobación de Python antes de Pandas |

Para agregar un proveedor, implementa el adaptador de `REGISTRO` con la firma existente, indica modelo, variable de credencial y timeout, y comprueba los dos contratos con las pruebas. Conserva la restricción de destino, los límites de red y el descarte de campos de razonamiento al implementar su transporte.

