#!/usr/bin/env Rscript
# =============================================================================
# 1_leer_datos.R
# -----------------------------------------------------------------------------
# Descripción
# -----------
# Limpieza y validación inicial de los datos brutos. Garantiza que 
# los registros tengan coordenadas válidas antes de la proyección.
#
# Precondiciones
# --------------
# - Entradas: config["datos_entrada"] (CSV).
# - Supuestos: Columnas 'longitud' y 'latitud' presentes en el archivo.
# - Entorno: qgis_env (R base + tidyverse).
#
# Resultados
# ----------
# - Salida: procesados/datos_filtrados.csv.
# - Criterio de éxito: Salida no vacía y sin NAs en coordenadas.
#
# Notas relevantes
# ----------------
# - Decisión: Se eliminan filas completas con NAs geográficos para evitar 
#   errores en las reglas subsiguientes.
# =============================================================================

library(readr)
library(dplyr)

# 1. Validación de precondiciones
input_file <- snakemake@input[["csv"]]
if (!file.exists(input_file)) {
  stop(paste("Archivo no encontrado:", input_file))
}

# 2. Carga y procesamiento
datos <- read_csv(input_file, show_col_types = FALSE)

datos_filtrados <- datos %>%
  filter(!is.na(longitud) & !is.na(latitud))

# 3. Exportación
write_csv(datos_filtrados, snakemake@output[["csv_filtrado"]])
message("Datos validados correctamente en: ", snakemake@output[["csv_filtrado"]])