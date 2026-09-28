# =========================================================
# CIUDAD AETHERA
# MISIÓN 4: AISLAMIENTO SOCIAL
# ANÁLISIS EXPLORATORIO DEL DATA PACK
# =========================================================


# =========================================================
# 0. INSTALAR PAQUETES
# =========================================================

# Ejecutar SOLO la primera vez.
# Después puedes dejar estas líneas comentadas.

# install.packages(c(
#   "tidyverse",
#   "sf",
#   "janitor",
#   "readxl"
# ))


# =========================================================
# 1. CARGAR LIBRERÍAS
# =========================================================

library(tidyverse)
library(sf)
library(janitor)
library(readxl)


# =========================================================
# 2. REVISAR CARPETA DE TRABAJO
# =========================================================

# Ver la carpeta actual
getwd()

# Ver qué archivos están dentro
list.files()

# Debieran aparecer:
# D1_wellbeing_survey.csv
# D2_support_services.csv
# D3_academic_trajectory.csv
# D6_services_map.geojson
# D7_calendar.csv
# DATA_DICTIONARY.xlsm


# =========================================================
# 3. CARGAR LOS ARCHIVOS
# =========================================================


# ---------------------------------------------------------
# D1: ENCUESTA DE BIENESTAR
# ---------------------------------------------------------

df_d1_survey <- read_csv(
  "D1_wellbeing_survey.csv",
  show_col_types = FALSE
) %>%
  clean_names()


# ---------------------------------------------------------
# D2: USO DE SERVICIOS DE APOYO
# ---------------------------------------------------------

df_d2_services <- read_csv(
  "D2_support_services.csv",
  show_col_types = FALSE
) %>%
  clean_names()


# ---------------------------------------------------------
# D3: TRAYECTORIA ACADÉMICA
# ---------------------------------------------------------

df_d3_trajectory <- read_csv(
  "D3_academic_trajectory.csv",
  show_col_types = FALSE
) %>%
  clean_names()


# ---------------------------------------------------------
# D6: MAPA DE SERVICIOS
# ---------------------------------------------------------

df_d6_map <- st_read(
  "D6_services_map.geojson",
  quiet = TRUE
) %>%
  clean_names()


# ---------------------------------------------------------
# D7: CALENDARIO ACADÉMICO
# ---------------------------------------------------------

df_d7_calendar <- read_csv(
  "D7_calendar.csv",
  show_col_types = FALSE
) %>%
  clean_names()


# =========================================================
# 4. REVISAR QUE TODO HAYA CARGADO BIEN
# =========================================================

glimpse(df_d1_survey)
glimpse(df_d2_services)
glimpse(df_d3_trajectory)
glimpse(df_d6_map)
glimpse(df_d7_calendar)


# Número de filas y columnas
dim(df_d1_survey)
dim(df_d2_services)
dim(df_d3_trajectory)
dim(df_d6_map)
dim(df_d7_calendar)


# Nombres de variables
names(df_d1_survey)
names(df_d2_services)
names(df_d3_trajectory)
names(df_d6_map)
names(df_d7_calendar)


# =========================================================
# 5. REVISAR DICCIONARIO DE DATOS
# =========================================================

# Ver las hojas disponibles
excel_sheets("DATA_DICTIONARY.xlsm")

# Las hojas incluyen:
# Overview
# D1
# D2
# D3
# D4
# D5
# D6
# D7
# Relationships
# Mission_Metrics

# Si quieres abrir una hoja específica:
diccionario_d1 <- read_excel(
  "DATA_DICTIONARY.xlsm",
  sheet = "D1"
)

diccionario_d1


# =========================================================
# 6. LÍNEA BASE MISIÓN 4
# =========================================================

# La variable relevante es:
# support_network
#
# Valores posibles:
# none
# limited
# adequate


tabla_red_apoyo <- df_d1_survey %>%
  count(
    support_network
  ) %>%
  mutate(
    porcentaje = n / sum(n) * 100
  )

tabla_red_apoyo


# Calcular específicamente estudiantes SIN red de apoyo

linea_base_m4 <- df_d1_survey %>%
  summarise(
    total_estudiantes = n(),
    
    sin_red = sum(
      support_network == "none",
      na.rm = TRUE
    ),
    
    porcentaje_sin_red =
      sin_red / total_estudiantes * 100
  )

linea_base_m4


# =========================================================
# 7. AISLAMIENTO SEGÚN CONDICIÓN MIGRATORIA
# =========================================================

tabla_migracion <- df_d1_survey %>%
  group_by(
    migration_status
  ) %>%
  summarise(
    total_estudiantes = n(),
    
    sin_red = sum(
      support_network == "none",
      na.rm = TRUE
    ),
    
    porcentaje_sin_red =
      sin_red / total_estudiantes * 100,
    
    .groups = "drop"
  )

tabla_migracion


# =========================================================
# 8. COMPOSICIÓN DEL GRUPO AISLADO
# =========================================================

# Queremos saber:
# dentro de TODOS los estudiantes sin red,
# qué porcentaje son migrantes internos.

composicion_aislados <- df_d1_survey %>%
  filter(
    support_network == "none"
  ) %>%
  count(
    migration_status
  ) %>%
  mutate(
    porcentaje = n / sum(n) * 100
  )

composicion_aislados


# =========================================================
# 9. AISLAMIENTO SEGÚN PARTICIPACIÓN UNIVERSITARIA
# =========================================================

tabla_participacion <- df_d1_survey %>%
  group_by(
    campus_activity_frequency
  ) %>%
  summarise(
    total_estudiantes = n(),
    
    sin_red = sum(
      support_network == "none",
      na.rm = TRUE
    ),
    
    porcentaje_sin_red =
      sin_red / total_estudiantes * 100,
    
    .groups = "drop"
  )

tabla_participacion


# =========================================================
# 10. INTERSECCIÓN:
# MIGRACIÓN + PARTICIPACIÓN UNIVERSITARIA
# =========================================================

tabla_interseccion <- df_d1_survey %>%
  group_by(
    migration_status,
    campus_activity_frequency
  ) %>%
  summarise(
    total_estudiantes = n(),
    
    sin_red = sum(
      support_network == "none",
      na.rm = TRUE
    ),
    
    porcentaje_sin_red =
      sin_red / total_estudiantes * 100,
    
    .groups = "drop"
  )

tabla_interseccion


# =========================================================
# 11. GRUPO PRIORITARIO
# =========================================================

# Migrantes internos +
# baja participación universitaria

grupo_prioritario <- df_d1_survey %>%
  filter(
    migration_status == "internal_migrant",
    campus_activity_frequency == "low"
  ) %>%
  summarise(
    total = n(),
    
    sin_red = sum(
      support_network == "none",
      na.rm = TRUE
    ),
    
    porcentaje_sin_red =
      sin_red / total * 100
  )

grupo_prioritario


# =========================================================
# 12. RED DE APOYO Y ANSIEDAD
# =========================================================

# IMPORTANTE:
# La variable correcta se llama anxiety_band
# NO anxiety_level.

tabla_ansiedad <- df_d1_survey %>%
  group_by(
    support_network
  ) %>%
  summarise(
    total = n(),
    
    ansiedad_moderada_alta = sum(
      anxiety_band %in% c(
        "moderate",
        "high"
      ),
      na.rm = TRUE
    ),
    
    porcentaje_ansiedad =
      ansiedad_moderada_alta /
      total * 100,
    
    .groups = "drop"
  )

tabla_ansiedad


# =========================================================
# 13. RED DE APOYO Y ESTRÉS
# =========================================================

tabla_estres <- df_d1_survey %>%
  group_by(
    support_network
  ) %>%
  summarise(
    total = n(),
    
    estres_moderado_alto = sum(
      stress_band %in% c(
        "moderate",
        "high"
      ),
      na.rm = TRUE
    ),
    
    porcentaje_estres =
      estres_moderado_alto /
      total * 100,
    
    .groups = "drop"
  )

tabla_estres


# =========================================================
# 14. PREPARAR DATOS PARA GRÁFICOS
# =========================================================


# ---------------------------------------------------------
# Migración
# ---------------------------------------------------------

tabla_migracion_grafico <- tabla_migracion %>%
  mutate(
    condicion_migratoria = case_when(
      
      migration_status == "local" ~
        "Estudiante local",
      
      migration_status == "internal_migrant" ~
        "Migrante interno",
      
      TRUE ~ migration_status
    )
  )


# ---------------------------------------------------------
# Participación
# ---------------------------------------------------------

tabla_participacion_grafico <- tabla_participacion %>%
  mutate(
    participacion = case_when(
      
      campus_activity_frequency == "low" ~
        "Baja",
      
      campus_activity_frequency == "medium" ~
        "Media",
      
      campus_activity_frequency == "high" ~
        "Alta",
      
      TRUE ~ campus_activity_frequency
    ),
    
    participacion = factor(
      participacion,
      levels = c(
        "Baja",
        "Media",
        "Alta"
      )
    )
  )


# =========================================================
# 15. GRÁFICO 1:
# AISLAMIENTO SEGÚN MIGRACIÓN
# =========================================================

grafico_migracion <- ggplot(
  tabla_migracion_grafico,
  aes(
    x = condicion_migratoria,
    y = porcentaje_sin_red,
    fill = condicion_migratoria
  )
) +
  
  geom_col(
    width = 0.65
  ) +
  
  geom_text(
    aes(
      label = paste0(
        round(
          porcentaje_sin_red,
          1
        ),
        "%"
      )
    ),
    
    vjust = -0.5,
    size = 5
  ) +
  
  labs(
    title =
      "Ausencia de red de apoyo según condición migratoria",
    
    subtitle =
      "Ciudad Aethera - Encuesta de Bienestar",
    
    x = NULL,
    
    y =
      "Estudiantes sin red de apoyo (%)"
  ) +
  
  coord_cartesian(
    ylim = c(
      0,
      max(
        tabla_migracion_grafico$
          porcentaje_sin_red
      ) + 10
    )
  ) +
  
  theme_minimal(
    base_size = 13
  ) +
  
  theme(
    legend.position = "none",
    
    plot.title =
      element_text(
        face = "bold"
      )
  )


grafico_migracion


# =========================================================
# 16. GRÁFICO 2:
# AISLAMIENTO SEGÚN PARTICIPACIÓN
# =========================================================

grafico_participacion <- ggplot(
  tabla_participacion_grafico,
  aes(
    x = participacion,
    y = porcentaje_sin_red,
    fill = participacion
  )
) +
  
  geom_col(
    width = 0.65
  ) +
  
  geom_text(
    aes(
      label = paste0(
        round(
          porcentaje_sin_red,
          1
        ),
        "%"
      )
    ),
    
    vjust = -0.5,
    size = 5
  ) +
  
  labs(
    title =
      "Ausencia de red de apoyo según participación universitaria",
    
    subtitle =
      "Ciudad Aethera - Encuesta de Bienestar",
    
    x =
      "Participación en actividades universitarias",
    
    y =
      "Estudiantes sin red de apoyo (%)"
  ) +
  
  coord_cartesian(
    ylim = c(
      0,
      max(
        tabla_participacion_grafico$
          porcentaje_sin_red
      ) + 10
    )
  ) +
  
  theme_minimal(
    base_size = 13
  ) +
  
  theme(
    legend.position = "none",
    
    plot.title =
      element_text(
        face = "bold"
      )
  )


grafico_participacion


# =========================================================
# 17. GRÁFICO 3:
# MIGRACIÓN + PARTICIPACIÓN
# =========================================================

tabla_interseccion_grafico <-
  tabla_interseccion %>%
  mutate(
    
    condicion_migratoria =
      case_when(
        
        migration_status == "local" ~
          "Estudiante local",
        
        migration_status ==
          "internal_migrant" ~
          "Migrante interno",
        
        TRUE ~
          migration_status
      ),
    
    participacion =
      case_when(
        
        campus_activity_frequency ==
          "low" ~
          "Baja",
        
        campus_activity_frequency ==
          "medium" ~
          "Media",
        
        campus_activity_frequency ==
          "high" ~
          "Alta",
        
        TRUE ~
          campus_activity_frequency
      ),
    
    participacion = factor(
      participacion,
      levels = c(
        "Baja",
        "Media",
        "Alta"
      )
    )
  )


grafico_interseccion <- ggplot(
  tabla_interseccion_grafico,
  aes(
    x = participacion,
    y = porcentaje_sin_red,
    fill = condicion_migratoria
  )
) +
  
  geom_col(
    position =
      position_dodge(
        width = 0.9
      )
  ) +
  
  geom_text(
    aes(
      label = paste0(
        round(
          porcentaje_sin_red,
          1
        ),
        "%"
      )
    ),
    
    position =
      position_dodge(
        width = 0.9
      ),
    
    vjust = -0.5,
    size = 4
  ) +
  
  labs(
    title =
      "Aislamiento social según migración y participación",
    
    subtitle =
      "Porcentaje de estudiantes que declara no tener red de apoyo",
    
    x =
      "Participación en actividades universitarias",
    
    y =
      "Estudiantes sin red de apoyo (%)",
    
    fill =
      "Condición migratoria"
  ) +
  
  coord_cartesian(
    ylim = c(0, 85)
  ) +
  
  theme_minimal(
    base_size = 13
  ) +
  
  theme(
    plot.title =
      element_text(
        face = "bold"
      ),
    
    legend.position =
      "top"
  )


grafico_interseccion


# =========================================================
# 18. GUARDAR LOS GRÁFICOS
# =========================================================

ggsave(
  filename =
    "grafico_migracion_m4.png",
  
  plot =
    grafico_migracion,
  
  width = 8,
  height = 5,
  dpi = 300
)


ggsave(
  filename =
    "grafico_participacion_m4.png",
  
  plot =
    grafico_participacion,
  
  width = 8,
  height = 5,
  dpi = 300
)


ggsave(
  filename =
    "grafico_interseccion_m4.png",
  
  plot =
    grafico_interseccion,
  
  width = 8,
  height = 5,
  dpi = 300
)


# =========================================================
# 19. TRAYECTORIA ACADÉMICA
# =========================================================

# D3 contiene varias observaciones
# del mismo estudiante porque existen
# distintos períodos académicos.
#
# NO unimos toda D3 directamente con D1.
#
# Usamos únicamente PER_2026_4,
# que es el período más próximo a la
# fecha de la encuesta de bienestar.


df_d3_periodo4 <- df_d3_trajectory %>%
  filter(
    period_id == "PER_2026_4"
  )


# Comprobar que haya una fila por estudiante
df_d3_periodo4 %>%
  count(
    student_id
  ) %>%
  filter(
    n > 1
  )


# =========================================================
# 20. UNIR D1 CON D3
# =========================================================

df_master <- df_d1_survey %>%
  left_join(
    df_d3_periodo4,
    by = "student_id",
    suffix = c(
      "_survey",
      "_academic"
    )
  )


glimpse(df_master)


# Comprobar número de filas
nrow(df_d1_survey)
nrow(df_master)


# Debieran ser iguales o muy similares,
# ya que ahora no estamos multiplicando
# estudiantes por cuatro períodos.


# =========================================================
# 21. RED DE APOYO Y DESEMPEÑO ACADÉMICO
# =========================================================

tabla_academica <- df_master %>%
  group_by(
    support_network
  ) %>%
  summarise(
    estudiantes = n(),
    
    promedio_nota =
      mean(
        average_grade,
        na.rm = TRUE
      ),
    
    asistencia_promedio =
      mean(
        attendance_rate,
        na.rm = TRUE
      ),
    
    .groups = "drop"
  )

tabla_academica


# =========================================================
# 22. RED DE APOYO Y ALERTA DE DESERCIÓN
# =========================================================

tabla_desercion <- df_master %>%
  filter(
    !is.na(dropout_alert)
  ) %>%
  count(
    support_network,
    dropout_alert
  ) %>%
  group_by(
    support_network
  ) %>%
  mutate(
    porcentaje =
      n / sum(n) * 100
  ) %>%
  ungroup()

tabla_desercion


# =========================================================
# 23. REVISAR SERVICIOS DISPONIBLES
# =========================================================

# Primero quitamos la geometría para trabajar
# como una tabla normal.

servicios_tabla <- df_d6_map %>%
  st_drop_geometry()


glimpse(servicios_tabla)


# Cantidad de servicios según tipo

tabla_tipos_servicio <- servicios_tabla %>%
  count(
    service_type,
    sort = TRUE
  )

tabla_tipos_servicio


# Servicios de apoyo entre pares

peer_support <- servicios_tabla %>%
  filter(
    service_type == "peer_support"
  ) %>%
  select(
    service_id,
    name,
    district_id,
    schedule,
    capacity
  )

peer_support


# Cantidad de apoyo entre pares por distrito

peer_support_distritos <- servicios_tabla %>%
  filter(
    service_type == "peer_support"
  ) %>%
  count(
    district_id
  )

peer_support_distritos


# =========================================================
# 24. REVISAR CALENDARIO ACADÉMICO
# =========================================================

# IMPORTANTE:
# La variable correcta es event_type.
# NO category.

tabla_eventos <- df_d7_calendar %>%
  count(
    event_type,
    sort = TRUE
  )

tabla_eventos


# =========================================================
# 25. ACTIVIDADES UNIVERSITARIAS
# =========================================================

actividades_universitarias <- df_d7_calendar %>%
  filter(
    event_type ==
      "university_activity"
  ) %>%
  select(
    calendar_event_id,
    period_id,
    title,
    start_date,
    end_date,
    institution_id,
    district_id
  )

actividades_universitarias


# Cantidad de actividades por distrito

actividades_por_distrito <-
  actividades_universitarias %>%
  count(
    district_id,
    sort = TRUE
  )

actividades_por_distrito


# Cantidad de actividades por institución

actividades_por_institucion <-
  actividades_universitarias %>%
  count(
    institution_id,
    sort = TRUE
  )

actividades_por_institucion


# =========================================================
# 26. SEMANAS DE BIENESTAR
# =========================================================

actividades_bienestar <- df_d7_calendar %>%
  filter(
    event_type ==
      "wellbeing_activity"
  )

actividades_bienestar


# =========================================================
# 27. USO DE SERVICIOS D2
# =========================================================

glimpse(df_d2_services)


# Motivos más frecuentes de consulta

motivos_servicio <- df_d2_services %>%
  count(
    reason_code,
    sort = TRUE
  )

motivos_servicio


# Resultado de derivaciones

resultados_derivacion <- df_d2_services %>%
  count(
    referral_outcome,
    sort = TRUE
  )

resultados_derivacion


# Tiempo promedio de espera

espera_servicios <- df_d2_services %>%
  summarise(
    promedio_dias =
      mean(
        wait_days,
        na.rm = TRUE
      ),
    
    mediana_dias =
      median(
        wait_days,
        na.rm = TRUE
      )
  )

espera_servicios


# =========================================================
# 28. USO DE SERVICIOS ENTRE ESTUDIANTES AISLADOS
# =========================================================

# Identificamos estudiantes sin red de apoyo.

ids_aislados <- df_d1_survey %>%
  filter(
    support_network == "none"
  ) %>%
  select(
    student_id
  )


# Buscamos si aparecen en D2

servicios_aislados <- df_d2_services %>%
  semi_join(
    ids_aislados,
    by = "student_id"
  )


# Cantidad de eventos de apoyo
nrow(servicios_aislados)


# Motivos de consulta del grupo aislado

motivos_aislados <- servicios_aislados %>%
  count(
    reason_code,
    sort = TRUE
  )

motivos_aislados


# =========================================================
# 29. GUARDAR TABLAS IMPORTANTES
# =========================================================

write_csv(
  tabla_red_apoyo,
  "tabla_red_apoyo_m4.csv"
)


write_csv(
  tabla_migracion,
  "tabla_migracion_m4.csv"
)


write_csv(
  tabla_participacion,
  "tabla_participacion_m4.csv"
)


write_csv(
  tabla_interseccion,
  "tabla_interseccion_m4.csv"
)


write_csv(
  tabla_ansiedad,
  "tabla_ansiedad_m4.csv"
)


write_csv(
  tabla_academica,
  "tabla_academica_m4.csv"
)


# =========================================================
# 30. RESULTADOS CLAVE EN CONSOLA
# =========================================================

cat(
  "\n==============================\n",
  "RESULTADOS CLAVE MISIÓN 4\n",
  "==============================\n\n"
)


print(
  linea_base_m4
)


cat(
  "\n--- AISLAMIENTO POR MIGRACIÓN ---\n"
)

print(
  tabla_migracion
)


cat(
  "\n--- AISLAMIENTO POR PARTICIPACIÓN ---\n"
)

print(
  tabla_participacion
)


cat(
  "\n--- MIGRACIÓN + PARTICIPACIÓN ---\n"
)

print(
  tabla_interseccion
)


cat(
  "\n--- GRUPO PRIORITARIO ---\n"
)

print(
  grupo_prioritario
)


cat(
  "\n--- RED DE APOYO Y ANSIEDAD ---\n"
)

print(
  tabla_ansiedad
)


# =========================================================
# FIN
# =========================================================