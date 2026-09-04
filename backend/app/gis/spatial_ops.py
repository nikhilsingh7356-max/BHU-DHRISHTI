import math
from typing import Optional
from shapely.geometry import shape, Polygon, MultiPolygon, box
from shapely.ops import unary_union


def calculate_area_from_geojson(geojson: dict) -> Optional[float]:
    if geojson is None:
        return None
    try:
        geom = shape(geojson)
        if geom.is_empty:
            return 0.0
        area = geom.area
        return round(area, 2)
    except Exception:
        return None


def check_geometry_validity(geojson: dict) -> bool:
    if geojson is None:
        return False
    try:
        geom = shape(geojson)
        return geom.is_valid and not geom.is_empty
    except Exception:
        return False


def check_parcel_overlap(geom1: dict, geom2: dict) -> bool:
    if geom1 is None or geom2 is None:
        return False
    try:
        g1 = shape(geom1)
        g2 = shape(geom2)
        if g1.is_empty or g2.is_empty:
            return False
        return g1.intersects(g2) and not g1.touches(g2)
    except Exception:
        return False


def calculate_bbox(geojson: dict) -> Optional[dict]:
    if geojson is None:
        return None
    try:
        geom = shape(geojson)
        bounds = geom.bounds
        return {
            "min_x": bounds[0],
            "min_y": bounds[1],
            "max_x": bounds[2],
            "max_y": bounds[3]
        }
    except Exception:
        return None


def calculate_centroid(geojson: dict) -> Optional[dict]:
    if geojson is None:
        return None
    try:
        geom = shape(geojson)
        centroid = geom.centroid
        return {"lat": centroid.y, "lon": centroid.x}
    except Exception:
        return None


def area_match_percentage(declared_area: float, geometry: dict, tolerance_percent: float = 5.0) -> bool:
    calc_area = calculate_area_from_geojson(geometry)
    if calc_area is None or declared_area is None or declared_area == 0:
        return False
    diff = abs(declared_area - calc_area)
    pct = (diff / declared_area) * 100
    return pct <= tolerance_percent
