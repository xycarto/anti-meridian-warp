import rasterio as rio
import geopandas as gp
from shapely.geometry import Polygon
from fiona.transform import transform_geom
from shapely.geometry import mapping, shape
import math
from osgeo import gdal
import os
import sys

## Example command:
# python3 project-across-meridian.py data/nzbathy_250m_nztm.tif

# World circumfrence in meters
WORLD_CIRCUM = 2 * math.pi * 6378137

in_file = sys.argv[1]
base_name = os.path.basename(in_file).split(".")[0]

# Get Raster Extent in Native Projection
in_rio = rio.open(in_file)

in_crs = in_rio.crs
minx = in_rio.bounds[0]
miny = in_rio.bounds[1]
maxx = in_rio.bounds[2]
maxy = in_rio.bounds[3]

native_poly = Polygon([[minx, miny],
                       [maxx, miny],
                       [maxx, maxy],
                       [minx, maxy],
                       [minx, miny]])

df = [{
    'geometry': native_poly
}]

native_extent = gp.GeoDataFrame(df, crs = in_crs)

# Reproject NZTM extents to WGS across antimeridian. This will create a MultiPolygon
poly =  shape(
            transform_geom(
                src_crs=native_extent.crs.to_wkt(),
                dst_crs="epsg:4326",
                geom=mapping(native_extent.geometry[0]),
                antimeridian_cutting=True,
            )
        )   

df_wgs = [{
    'geometry': poly
}]

wgs_extent = gp.GeoDataFrame(df_wgs, crs = "epsg:4326")

# wgs_extent.to_file("data/wgs_extent.gpkg", driver="GPKG")

# Get new X Max from left poly
wgs_multi_left = wgs_extent.explode().iloc[1]
wgs_poly_left = wgs_multi_left.geometry
df_wgs_edge_left = [{
    'geometry': wgs_poly_left
}]

wgs_edge_extent_left = gp.GeoDataFrame(df_wgs_edge_left, crs = "epsg:4326")

## Shift left polygon around the globe using 360 degrees
anti_maxx = wgs_edge_extent_left.total_bounds[2] + 360

# Get new X Min from right poly
wgs_multi_right = wgs_extent.explode().iloc[0]
wgs_poly_right = wgs_multi_right.geometry
df_wgs_edge_right = [{
    'geometry': wgs_poly_right
}]

wgs_edge_extent_right = gp.GeoDataFrame(df_wgs_edge_right, crs = "epsg:4326")

anti_minx = wgs_edge_extent_right.total_bounds[0]

## Build new WGS Poly
wgs_anti_poly = Polygon([[anti_minx, wgs_extent.total_bounds[1]],
                      [anti_maxx, wgs_extent.total_bounds[1]],
                      [anti_maxx, wgs_extent.total_bounds[3]],
                      [anti_minx, wgs_extent.total_bounds[3]],
                      [anti_minx, wgs_extent.total_bounds[1]]])

df_anti = [{
    'geometry': wgs_anti_poly
}]

wgs_anti_extent = gp.GeoDataFrame(df_anti, crs = "epsg:4326")

# wgs_anti_extent.to_file("data/wgs_anti_extent.gpkg", driver="GPKG")

# Shift webmer poly over merdiain
webmer_anti = wgs_anti_extent.to_crs(3857)

shift_maxx = webmer_anti.total_bounds[0] + WORLD_CIRCUM
shift_minx = webmer_anti.total_bounds[2]

## Build new Webmer Poly over Anti-Meridian
webmer_anti_poly = Polygon([[shift_minx, webmer_anti.total_bounds[1]],
                      [shift_maxx, webmer_anti.total_bounds[1]],
                      [shift_maxx, webmer_anti.total_bounds[3]],
                      [shift_minx, webmer_anti.total_bounds[3]],
                      [shift_minx, webmer_anti.total_bounds[1]]])

df_webmer_anti = [{
    'geometry': webmer_anti_poly
}]

webmer_anti_extent = gp.GeoDataFrame(df_webmer_anti, crs = "epsg:3857")

# webmer_anti_extent.to_file('data/webmer_anti.gpkg', driver='GPKG')

# Reproject
print("Warping to Web Mecator...")
gdal.Warp(
    "data/niwa_250_webmer.tif",
    in_file,
    format = 'GTiff',
    outputBounds = (webmer_anti_extent.total_bounds[0],
                    webmer_anti_extent.total_bounds[1],
                    webmer_anti_extent.total_bounds[2],
                    webmer_anti_extent.total_bounds[3]),
    srcSRS = in_crs,
    dstSRS = 'EPSG:3857',
    xRes = 250, 
    yRes = 250, 
    callback=gdal.TermProgress_nocb
    )