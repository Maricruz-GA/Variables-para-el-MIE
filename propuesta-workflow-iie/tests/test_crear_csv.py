import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch
from affine import Affine
import rasterio

# Importamos las funciones necesarias del script
from s1_crear_csv_reg_tifs import build_valid_mask, process_one_malla

## 1. Test unitario (Lógica de máscara)
def test_build_valid_mask():
    # PREPARAR: Datos de entrada controlados
    data = np.array([[1, 2], [3, 4]])
    mask = np.array([[False, False], [True, False]])
    malla_arr = np.ma.masked_array(data, mask=mask)

    # EJECUTAR: La función sometida a test
    res = build_valid_mask(malla_arr, nodata=None)

    # VERIFICAR: ¿El resultado es el que esperábamos lógicamente?
    assert res[0, 0] == True
    assert res[1, 0] == False

## 2. Test de integración (Corrigiendo la validación de la transformación Affine)
@patch("rasterio.open")
@patch("s1_crear_csv_reg_tifs.get_pixel_centers")
def test_process_one_malla(mock_get_centers, mock_open):

    # Definimos la transformación real para que pase el isinstance(transform, Affine)
    transform_real = Affine(1, 0, 100, 0, -1, 201)
    
    # Coordenadas 2x2 reales
    xs = np.array([[100.5, 101.5], [100.5, 101.5]])
    ys = np.array([[200.5, 200.5], [199.5, 199.5]])
    mock_get_centers.return_value = (xs, ys)

    # --- DATOS DE PRUEBA REALISTAS ---
    malla_data = np.array([[1, 1], [1, 1]], dtype=np.int32)
    malla_masked = np.ma.masked_array(malla_data, mask=False)
    
    tif_data = np.array([[10, 20], [30, 40]], dtype=np.float32)
    tif_masked = np.ma.masked_array(tif_data, mask=False)

    # --- CONFIGURACIÓN MOCK MALLA ---
    malla_src = MagicMock()
    malla_src.width = 2
    malla_src.height = 2
    malla_src.transform = transform_real # <--- OBJETO REAL AQUÍ
    malla_src.bounds = (100, 199, 102, 201)
    malla_src.nodata = None
    malla_src.read.return_value = malla_masked
    malla_src.__enter__.return_value = malla_src

    # --- CONFIGURACIÓN MOCK TIF VARIABLE ---
    tif_src = MagicMock()
    tif_src.transform = transform_real # <--- OBJETO REALISTA AQUÍ TAMBIÉN
    tif_src.read.return_value = tif_masked

    # El script llama a window_transform, devolvemos un Affine real
    tif_src.window_transform.return_value = transform_real
    tif_src.__enter__.return_value = tif_src

    # Rasterio.open devolverá primero la malla y luego el tif
    mock_open.side_effect = [malla_src, tif_src]

    # EJECUCIÓN
    malla_path = Path("malla.tif") # Datos de prueba tipo geotif
    tif_paths = [Path("temp.tif")] 
    df = process_one_malla(malla_path, tif_paths) 

    # VALIDACIONES
    # Cada línea es una pregunta. Sólo se responde como cierta/falsa 
    assert isinstance(df, pd.DataFrame) 
    assert len(df) == 4
    assert "temp" in df.columns
    assert df["mallaid"].iloc[0] == 1
    assert df["temp"].iloc[0] == 10