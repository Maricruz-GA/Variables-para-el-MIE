#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================================
6_agregar_datos.py
-----------------------------------------------------------------------------

Descripción
-----------
- Escanea de forma recursiva el directorio 'resultados/' en busca de archivos 
  GeoTIFF y GeoPackage para consolidarlos en un dataset tabular plano.
- Extrae los valores de píxel de capas ráster y la primera columna de atributos 
  de capas vectoriales asociándolos al centroide de la retícula base.

Precondiciones
--------------
- Entrada: El GeoPackage base de polígonos indexado en snakemake.input[0].
- Carpeta: Un subárbol de archivos 'resultados/' con productos geoespaciales.
- Entorno: qgis_env (requiere geopandas, rasterio, shapely).

Resultados
----------
- Salida: resultados/dataset_agregado.csv (definido en snakemake.output[0]).
- Producto: CSV plano con estructura: id, longitud, latitud, [coberturas...].
- Criterio de éxito: El archivo CSV contiene columnas separadas para el valor 
  del ráster y el atributo del GeoPackage de origen.

Notas relevantes
----------------
- Diseño: Para evitar distorsiones y advertencias en el cálculo de centroides 
  y sjoin_nearest, las operaciones espaciales se ejecutan temporalmente en 
  un CRS métrico (EPSG:6372) antes de extraer coordenadas WGS84.
=============================================================================
"""

import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.sample import sample_gen
import os
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extraer_valores_raster(centroides_wgs84, raster_path):
    """Extrae valores de un ráster usando las coordenadas de los centroides en WGS84."""
    try:
        with rasterio.open(raster_path) as src:
            coords = [(x, y) for x, y in zip(centroides_wgs84.geometry.x, centroides_wgs84.geometry.y)]
            return [val[0] for val in sample_gen(src, coords)]
    except Exception as e:
        logging.warning(f"No se pudo procesar el ráster {raster_path}: {e}")
        return [None] * len(centroides_wgs84)

def main():
    try:
        gpkg_path = snakemake.input[0]
        output_csv = snakemake.output[0]
        
        logging.info(f"Cargando retícula poligonal base: {gpkg_path}")
        gdf_poligonos = gpd.read_file(gpkg_path)
        
        CRS_METRICO = "EPSG:6372"
        if gdf_poligonos.crs != CRS_METRICO:
            gdf_poligonos = gdf_poligonos.to_crs(CRS_METRICO)
            
        gdf_centroides_m = gdf_poligonos.copy()
        gdf_centroides_m["geometry"] = gdf_poligonos.geometry.centroid
        
        gdf_centroides_wgs84 = gdf_centroides_m.to_crs("EPSG:4326")
        
        df_final = pd.DataFrame({
            'id': range(1, len(gdf_centroides_wgs84) + 1),
            'longitud': gdf_centroides_wgs84.geometry.x,
            'latitud': gdf_centroides_wgs84.geometry.y
        })
        
        for root, _, files in os.walk("resultados/"):
            for file in files:
                path = os.path.join(root, file)
                nombre_col = os.path.splitext(file)[0].replace(" ", "_").replace("-", "_")
                
                if file.endswith(('.tif', '.tiff')):
                    logging.info(f" -> Muestreando píxeles de Ráster: {nombre_col}")
                    df_final[nombre_col] = extraer_valores_raster(gdf_centroides_wgs84, path)
                    
                elif file.endswith('.gpkg'):
                    logging.info(f" -> Ejecutando Proximidad Vectorial: {nombre_col}")
                    try:
                        temp_gdf = gpd.read_file(path).to_crs(CRS_METRICO)
                        columnas_datos = [c for c in temp_gdf.columns if c != 'geometry' and not c.startswith('index_')]
                        
                        if columnas_datos:
                            primera_col_valor = columnas_datos[0]
                            temp_minimo = temp_gdf[[primera_col_valor, 'geometry']].copy()
                            temp_minimo = temp_minimo.rename(columns={primera_col_valor: nombre_col})
                            
                            joined = gpd.sjoin_nearest(gdf_centroides_m, temp_minimo, how='left')
                            df_final[nombre_col] = joined[nombre_col].values
                        else:
                            df_final[nombre_col] = None
                            
                    except Exception as e:
                        logging.warning(f"Error en join espacial con {file}: {e}")

        df_final.to_csv(output_csv, index=False)
        logging.info(f"Éxito. Dataset consolidado de puntos en: {output_csv}")

    except Exception as e:
        logging.error(f"Falla crítica: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
