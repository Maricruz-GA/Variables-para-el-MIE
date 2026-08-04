#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=============================================================================
3_crear_reticula.py
-----------------------------------------------------------------------------

Descripción
-----------
Genera un archivo GeoPackage que contiene una retícula (grilla) vectorial 
regular a partir de un dataset de puntos. Se utiliza en la Rama 1 del 
workflow (Enfoque Vectorial) para espacializar datos tabulares en una 
resolución fija.

Precondiciones
--------------
- Entrada: datos/registros_base.csv (debe contener columnas 'latitud' y 'longitud').
- Entorno: Requiere el entorno 'qgis_env' con geopandas, numpy y shapely.
- CRS: Se asume entrada en EPSG:4326.

Resultados
----------
- Salida: resultados/reticula_variable.gpkg.
- Producto: GeoPackage vectorial con geometría de polígonos (celdas).
- Criterio de éxito: Archivo generado en la ruta de salida con geometría válida.

Notas relevantes
----------------
- Advertencia técnica: La construcción de la grilla se realiza internamente 
  en un CRS métrico (EPSG:6372) para asegurar la precisión del tamaño del píxel.
- Diseño: La función `create_pixel_box_metric` permite realizar el "snap" 
  de los puntos a una grilla regular según el parámetro de resolución.
=============================================================================
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
import numpy as np


input_csv = snakemake.input["csv_puntos"]
output_gpkg = snakemake.output["gpkg"]
pixel_size_metros = float(snakemake.params["res"])

LAYER_NAME = "reticula_variable"

# CRS de entrada y salida para publicación
CRS_LONLAT = "EPSG:4326"

# CRS métrico para construir la retícula.
# Si EPSG:6372 diera problemas en tu entorno, cambia temporalmente a EPSG:3857.
CRS_METRICO = "EPSG:6372"


def create_pixel_box_metric(point, res_m):
    """
    Encaja un punto en una malla regular definida en metros.
    """
    x_snap = np.floor(point.x / res_m) * res_m
    y_snap = np.floor(point.y / res_m) * res_m

    return box(
        x_snap,
        y_snap,
        x_snap + res_m,
        y_snap + res_m
    )


def main():
    df = pd.read_csv(input_csv)

    col_valor = "valor_iie" if "valor_iie" in df.columns else "valor_indice"

    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["longitud"], df["latitud"])],
        crs=CRS_LONLAT
    )

    # 1. Pasar a CRS métrico
    gdf_m = gdf.to_crs(CRS_METRICO)

    # 2. Crear celdas en metros
    gdf_m["geometry"] = gdf_m.geometry.apply(
        lambda p: create_pixel_box_metric(p, pixel_size_metros)
    )

    # 3. Agregar puntos que caen en la misma celda
    gdf_m["cell_id"] = gdf_m.geometry.apply(lambda geom: geom.wkb_hex)

    grid = (
        gdf_m
        .groupby("cell_id", as_index=False)
        .agg({
            col_valor: "mean",
            "geometry": "first"
        })
    )

    grid = gpd.GeoDataFrame(
        grid,
        geometry="geometry",
        crs=CRS_METRICO
    )

    # 4. Reproyectar a EPSG:4326 para publicación
    grid = grid.to_crs(CRS_LONLAT)

    # 5. Esquema estable para reportes y cartografía
    grid["valor_indice"] = grid[col_valor]
    grid["integridad_simulada"] = grid[col_valor]

    # 6. Limpieza de columna técnica
    grid = grid.drop(columns=["cell_id"])

    # 7. Exportar GeoPackage con nombre de capa explícito
    grid.to_file(
        output_gpkg,
        layer=LAYER_NAME,
        driver="GPKG"
    )

    print(f"GeoPackage generado: {output_gpkg}")
    print(f"Capa: {LAYER_NAME}")
    print(f"CRS salida: {CRS_LONLAT}")
    print(f"Resolución usada en CRS métrico: {pixel_size_metros} m")
    print(f"Features: {len(grid)}")
    print(f"Bounds EPSG:4326: {grid.total_bounds}")


if __name__ == "__main__":
    main()