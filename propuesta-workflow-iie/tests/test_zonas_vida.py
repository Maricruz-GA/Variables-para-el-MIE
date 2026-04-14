import pytest
from unittest.mock import MagicMock, patch
from osgeo import gdal
import os 

# Importamos las funciones del nuevo script
# Recuerda que el script debe llamarse zonas_vida_headless.py (sin el 1_ inicial y sin guiones)
from zonas_de_vida_headless import dataset_info, warp_to_template

## 1. TEST UNITARIO: Lógica de extracción de metadatos
def test_dataset_info():
    """
    Identificar: Extraer info geográfica de un dataset.
    Producir: Un mock que simule un GDAL Dataset.
    Alimentar: Pasar el mock a dataset_info.
    Verificar: Que los cálculos de extensión (xmin, ymax, etc.) sean correctos.
    """
    # Arrange (Organizar)
    mock_ds = MagicMock()
    # GeoTransform: (origin_x, pixel_width, 0, origin_y, 0, pixel_height)
    mock_ds.GetGeoTransform.return_value = (100.0, 1.0, 0.0, 500.0, 0.0, -1.0)
    mock_ds.GetProjection.return_value = "EPSG:4326"
    mock_ds.RasterXSize = 10
    mock_ds.RasterYSize = 10

    # Act (Actuar)
    info = dataset_info(mock_ds, "test_raster")

    # Assert (Verificar)
    assert info["xmin"] == 100.0
    assert info["xmax"] == 110.0  # 100 + (1.0 * 10)
    assert info["ymin"] == 490.0  # 500 + (-1.0 * 10)
    assert info["projection"] == "EPSG:4326"

## 2. TEST DE INTEGRACIÓN: Simulación de GDAL Warp
@patch("osgeo.gdal.Open")
@patch("osgeo.gdal.Warp")
def test_warp_to_template(mock_warp, mock_open):
    """
    Este test verifica que enviamos los parámetros correctos a GDAL Warp
    sin necesidad de abrir archivos reales.
    """
    # Arrange
    template_info = {
        "projection": "EPSG:4326",
        "pixel_width": 1.0,
        "pixel_height": -1.0,
        "xmin": 100, "ymin": 0, "xmax": 200, "ymax": 100
    }
    
    # Simulamos que el archivo de origen se abre correctamente
    mock_src_ds = MagicMock()
    mock_src_ds.GetProjection.return_value = "EPSG:4326"
    mock_open.return_value = mock_src_ds
    
    # Simulamos que Warp genera un dataset de salida exitoso
    mock_warp.return_value = MagicMock()

    # Act
    # Usamos patch de os.path.isfile para que el script crea que el archivo se creó
    with patch("os.path.isfile", return_value=True):
        warp_to_template("origen.tif", template_info, "destino.tif")

    # Assert: ¿Llamamos a Warp con los límites de la plantilla?
    # Obtenemos los argumentos con los que se llamó a Warp
    args, kwargs = mock_warp.call_args
    assert kwargs["dstSRS"] == "EPSG:4326"
    assert kwargs["outputBounds"] == (100, 0, 200, 100)
    assert kwargs["resampleAlg"] == "near"  