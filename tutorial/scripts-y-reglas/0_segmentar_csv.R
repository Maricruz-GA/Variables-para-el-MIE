#!/usr/bin/env Rscript
# =============================================================================
# 0_segmentar_csv.R
# -----------------------------------------------------------------------------
# Descripción
# -----------
# Divide un dataset maestro masivo en subconjuntos regionales. 
# Se usa en la fase inicial del workflow para permitir el procesamiento en paralelo (Scatter).
#
# Precondiciones
# --------------
# - Entradas: datos/registros_base.csv.
# - Supuestos: El CSV contiene la columna 'id_region'.
# - Entorno: qgis_env (R base + tidyverse).
#
# Resultados
# ----------
# - Salida: archivos en procesados/datos_{region}.csv.
# - Criterio de éxito: Generación de un archivo por cada región listada.
#
# Notas relevantes
# ----------------
# - Diseño: Utiliza group_walk para una escritura eficiente sin cargar memoria.
# =============================================================================

library(readr)
library(dplyr)
library(purrr)

archivo_entrada <- snakemake@input[["csv"]]
if (!file.exists(archivo_entrada)) stop("Archivo entrada no encontrado")

datos_maestros <- read_csv(archivo_entrada, show_col_types = FALSE)

datos_maestros %>%
  group_by(id_region) %>%
  group_walk(~ {
    ruta_salida <- paste0("procesados/datos_", .y$id_region, ".csv")
    write_csv(.x, ruta_salida)
    message("Segmento escrito: ", ruta_salida)
  })
  