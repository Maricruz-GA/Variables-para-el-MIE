from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin

from create_ie_raster import (
    normalize_ie_predictions,
    build_reference_grid_map,
    find_reference_raster,
    sort_regions_numerically,
    build_source_grid_from_points,
    warp_source_to_template,
    rasterize_points_to_template,
)


def test_normalize_ie_predictions():
    values = np.array([1.5, 3.5, 5.5], dtype=float)
    out = normalize_ie_predictions(values)
    assert np.allclose(out, np.array([0.0, 0.5, 1.0]))


def test_sort_regions_numerically():
    regions = ["region_1", "region_10", "region_2", "region_3"]
    out = sort_regions_numerically(regions)
    assert out == ["region_1", "region_2", "region_3", "region_10"]


def test_build_reference_grid_map(tmp_path: Path):
    (tmp_path / "region_1").mkdir()
    (tmp_path / "region_2").mkdir()

    (tmp_path / "region_1" / "ref_grid.tif").touch()
    (tmp_path / "region_2" / "ref_grid.tif").touch()

    mapping = build_reference_grid_map(tmp_path)

    assert set(mapping.keys()) == {"region_1", "region_2"}
    assert mapping["region_1"].name == "ref_grid.tif"
    assert mapping["region_2"].name == "ref_grid.tif"


def test_find_reference_raster():
    mapping = {
        "region_1": Path("/tmp/region_1/ref_grid.tif"),
        "region_2": Path("/tmp/region_2/ref_grid.tif"),
    }

    out = find_reference_raster("region_1", mapping)
    assert out == Path("/tmp/region_1/ref_grid.tif")


def test_find_reference_raster_raises():
    mapping = {"region_1": Path("/tmp/region_1/ref_grid.tif")}

    with pytest.raises(FileNotFoundError):
        find_reference_raster("region_99", mapping)


def test_build_source_grid_from_points():
    region_df = pd.DataFrame(
        {
            "regionId": ["region_1", "region_1", "region_1", "region_1"],
            "x": [-100.0, -99.5, -100.0, -99.5],
            "y": [20.5, 20.5, 20.0, 20.0],
            "idx": [1, 2, 3, 4],
        }
    )

    ie_pred_values = np.array([0.1, 0.2, 0.3, 0.4], dtype=float)

    source_array, transform = build_source_grid_from_points(
        region_df=region_df,
        ie_pred_values=ie_pred_values,
        nodata_value=-9999.0,
    )

    assert source_array.shape == (2, 2)

    valid = source_array[source_array != -9999.0]
    assert valid.size == 4
    assert np.isclose(valid.min(), 0.1)
    assert np.isclose(valid.max(), 0.4)

    # Verificación básica de transform
    assert transform.a > 0
    assert transform.e < 0


def test_build_source_grid_from_points_averages_duplicates():
    region_df = pd.DataFrame(
        {
            "regionId": ["region_1", "region_1"],
            "x": [-100.0, -100.0],
            "y": [20.0, 20.0],
            "idx": [1, 2],
        }
    )

    ie_pred_values = np.array([0.2, 0.6], dtype=float)

    with pytest.raises(ValueError):
        # La función requiere al menos dos coordenadas únicas en x e y
        build_source_grid_from_points(
            region_df=region_df,
            ie_pred_values=ie_pred_values,
            nodata_value=-9999.0,
        )


def test_warp_source_to_template(tmp_path: Path):
    source_array = np.array(
        [
            [0.1, 0.2],
            [0.3, 0.4],
        ],
        dtype="float32",
    )

    source_transform = from_origin(-100.25, 20.75, 0.5, 0.5)

    template_path = tmp_path / "ref_grid.tif"
    output_path = tmp_path / "out.tif"

    width = 2
    height = 2
    template_transform = from_origin(-100.25, 20.75, 0.5, 0.5)

    meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": template_transform,
        "nodata": -9999.0,
    }

    with rasterio.open(template_path, "w", **meta) as dst:
        dst.write(np.full((1, height, width), -9999.0, dtype="float32"))

    valid_count, min_valid, max_valid = warp_source_to_template(
        source_array=source_array,
        source_transform=source_transform,
        template_path=template_path,
        output_path=output_path,
        source_crs="EPSG:4326",
        nodata_value=-9999.0,
    )

    assert output_path.exists()
    assert valid_count == 4
    assert min_valid == pytest.approx(0.1)
    assert max_valid == pytest.approx(0.4)

    with rasterio.open(output_path) as src:
        arr = src.read(1)
        assert arr.shape == (2, 2)
        assert src.nodata == -9999.0
        valid = arr[arr != -9999.0]
        assert valid.size == 4


def test_rasterize_points_to_template_same_crs(tmp_path: Path):
    template_path = tmp_path / "ref_grid.tif"
    output_path = tmp_path / "out.tif"

    width = 2
    height = 2
    transform = from_origin(-100.25, 20.75, 0.5, 0.5)

    meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": -9999.0,
    }

    with rasterio.open(template_path, "w", **meta) as dst:
        dst.write(np.full((1, height, width), -9999.0, dtype="float32"))

    region_df = pd.DataFrame(
        {
            "regionId": ["region_1", "region_1", "region_1", "region_1"],
            "x": [-100.0, -99.5, -100.0, -99.5],
            "y": [20.5, 20.5, 20.0, 20.0],
            "idx": [1, 2, 3, 4],
        }
    )

    ie_pred_values = np.array([0.11, 0.22, 0.33, 0.44], dtype=float)

    valid_count, min_valid, max_valid = rasterize_points_to_template(
        region_df=region_df,
        ie_pred_values=ie_pred_values,
        template_path=template_path,
        output_path=output_path,
        source_crs="EPSG:4326",
        nodata_value=-9999.0,
    )

    assert output_path.exists()
    assert valid_count == 4
    assert min_valid == pytest.approx(0.11)
    assert max_valid == pytest.approx(0.44)

    with rasterio.open(output_path) as src:
        arr = src.read(1)
        valid = arr[arr != -9999.0]
        assert valid.size == 4
        assert np.isclose(valid.min(), 0.11)
        assert np.isclose(valid.max(), 0.44)


def test_rasterize_points_to_template_overwrites_existing_file(tmp_path: Path):
    template_path = tmp_path / "ref_grid.tif"
    output_path = tmp_path / "out.tif"

    width = 2
    height = 2
    transform = from_origin(-100.25, 20.75, 0.5, 0.5)

    meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": -9999.0,
    }

    with rasterio.open(template_path, "w", **meta) as dst:
        dst.write(np.full((1, height, width), -9999.0, dtype="float32"))

    # archivo previo
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(np.ones((1, height, width), dtype="float32"))

    region_df = pd.DataFrame(
        {
            "regionId": ["region_1", "region_1", "region_1", "region_1"],
            "x": [-100.0, -99.5, -100.0, -99.5],
            "y": [20.5, 20.5, 20.0, 20.0],
            "idx": [1, 2, 3, 4],
        }
    )

    ie_pred_values = np.array([0.5, 0.6, 0.7, 0.8], dtype=float)

    rasterize_points_to_template(
        region_df=region_df,
        ie_pred_values=ie_pred_values,
        template_path=template_path,
        output_path=output_path,
        source_crs="EPSG:4326",
        nodata_value=-9999.0,
    )

    with rasterio.open(output_path) as src:
        arr = src.read(1)
        valid = arr[arr != -9999.0]
        assert valid.size == 4
        assert np.isclose(valid.min(), 0.5)
        assert np.isclose(valid.max(), 0.8)