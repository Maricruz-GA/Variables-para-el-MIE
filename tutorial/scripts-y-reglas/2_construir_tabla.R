#!/usr/bin/env Rscript
# =============================================================================
# 2_construir_tabla.R
# -----------------------------------------------------------------------------
# Descripción
# -----------
# Genera métricas estadísticas de integridad por región y tipo de ecosistema.
#
# Precondiciones
# --------------
# - Entradas: procesados/datos_filtrados.csv.
# - Supuestos: Columnas 'id_region', 'tipo_ecosistema', 'valor_indice'.
#
# Resultados
# ----------
# - Salida: resultados/tabla_atributos.csv.
# - Criterio de éxito: Tabla con columnas de media y conteo.
# =============================================================================

library(readr)
library(dplyr)

datos_f <- read_csv(snakemake@input[["csv_filtrado"]], show_col_types = FALSE)

tabla_atributos <- datos_f %>%
  group_by(id_region, tipo_ecosistema) %>%
  summarise(
    media_integridad = mean(valor_indice, na.rm = TRUE),
    conteo_registros = n(),
    .groups = 'drop'
  )

write_csv(tabla_atributos, snakemake@output[["tabla_resumen"]])
message("Resumen de atributos generado en: ", snakemake@output[["tabla_resumen"]])