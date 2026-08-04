#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=============================================================================
4_crear_raster_regional.py
-----------------------------------------------------------------------------
Descripción
-----------
- Rasteriza datos vectoriales en una matriz GeoTIFF optimizada.
- Se usa en la Rama 2 para Big Data.

Precondiciones
--------------
- Entradas: procesados/datos_{region}.csv.
- Dependencias: geopandas, rasterio, numpy.

Resultados
----------
- Salida: procesados/reticula_{region}.tif.
- Criterio de éxito: Archivo TIFF válido y georreferenciado.
=============================================================================
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import rasterio
from rasterio.transform import from_bounds
from rasterio.features import rasterize
import sys
import logging

logging.basicConfig(level=logging.INFO)

def main():
    input_csv = snakemake.input["csv_region"]
    output_tif = snakemake.output["tif_region"]
    res = float(snakemake.params["res"])
    
    df = pd.read_csv(input_csv)
    gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df['longitud'], df['latitud'])], crs="EPSG:4326")
    
    xmin, ymin, xmax, ymax = gdf.total_bounds
    res_grados = res / 111000.0
    width = int((xmax - xmin) / res_grados) + 1
    height = int((ymax - ymin) / res_grados) + 1
    transform = from_bounds(xmin, ymin, xmax, ymax, width, height)
    
    shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf['valor_indice']))
    matriz = rasterize(shapes=shapes, out_shape=(height, width), transform=transform, fill=-9999)
    
    with rasterio.open(output_tif, 'w', driver='GTiff', height=height, width=width, count=1, dtype='float32', transform=transform, crs="EPSG:4326") as dst:
        dst.write(matriz, 1)
    logging.info(f"Raster generado: {output_tif}")

if __name__ == "__main__":
    main()