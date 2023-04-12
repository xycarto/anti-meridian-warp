import rasterio as rio
import os
os.environ['USE_PYGEOS'] = '0'
import geopandas as gp
from shapely.geometry import Polygon
from fiona.transform import transform_geom
from shapely.geometry import mapping, shape, box
import math
from osgeo import gdal
import sys
import rioxarray
from rioxarray.merge import merge_datasets

## Example command:
# python3 anti-meridian-warp.py data/nzbathy_250m_nztm.tif


def main(in_file):
    
    native_extent, in_crs = get_native_extent(in_file)
    wgs_extent = repro_wgs(native_extent)
    anti_maxx, anti_minx = new_x_minmax(wgs_extent)
    wgs_anti_extent = wgs_poly(anti_minx, anti_maxx, wgs_extent)
    webmer_anti_extent = webmer_shift(wgs_anti_extent)
    
    print(webmer_anti_extent.total_bounds)
    
    # Reproject
    # print("Warping to Web Mecator...")
    # rio_in = rioxarray.open_rasterio(in_file, decode_coords="all")
    # repro = rio_in.rio.reproject('epsg:3857', inplace=True)
    # repro.rio.to_raster("data/rio.tif")
    gdal.Warp(
        "data/niwa_250_webmer.tif",
        in_file,
        format = 'GTiff',
        outputBounds = (webmer_anti_extent.total_bounds[0],
                        webmer_anti_extent.total_bounds[1],
                        webmer_anti_extent.total_bounds[2],
                        webmer_anti_extent.total_bounds[3]),
        outputBoundsSRS = 'EPSG:3857',
        srcSRS = in_crs,
        dstSRS = 'EPSG:3857',
        xRes = 250, 
        yRes = 250, 
        callback=gdal.TermProgress_nocb
        )
    
def get_native_extent(in_file):        
    # Get coords
    in_rio = rio.open(in_file)
    in_crs = in_rio.crs
    native_poly = box(*in_rio.bounds)

    # To GDF
    native_extent = gp.GeoDataFrame(index=[0], crs=in_crs, geometry=[native_poly])
    # native_extent.to_file("data/native.gpkg", driver="GPKG")

    return native_extent, in_crs

def repro_wgs(native_extent):
    wgs_poly = shape(
        transform_geom(
            src_crs=native_extent.crs.to_wkt(),
            dst_crs="epsg:4326",
            geom=mapping(native_extent.geometry[0]),
            antimeridian_cutting=True,
        )
    )
    wgs_extent =  gp.GeoDataFrame(index=[0], crs="epsg:4326", geometry=[wgs_poly])
    wgs_extent.to_file("data/wgs.gpkg", driver="GPKG")
    
    return wgs_extent

def new_x_minmax(wgs_extent):
    # Get new X Max from left poly
    wgs_multi_left = wgs_extent.explode(index_parts=True).iloc[0]
    wgs_edge_extent_left =  gp.GeoDataFrame(index=[0], crs = "epsg:4326", geometry=[wgs_multi_left.geometry])

    ## Shift left polygon around the globe using 360 degrees
    anti_maxx = wgs_edge_extent_left.total_bounds[2] + 360

    # Get new X Min from right poly
    wgs_multi_right = wgs_extent.explode(index_parts=True).iloc[1]

    wgs_edge_extent_right = gp.GeoDataFrame(index=[0], crs = "epsg:4326", geometry=[wgs_multi_right.geometry])

    anti_minx = wgs_edge_extent_right.total_bounds[0]
    
    wgs_edge_extent_left.to_file("data/left.gpkg", driver="GPKG")
    wgs_edge_extent_right.to_file("data/right.gpkg", driver="GPKG")    
    
    return anti_maxx, anti_minx

def wgs_poly(anti_minx, anti_maxx, wgs_extent):
    wgs_anti_poly = Polygon([[anti_minx, wgs_extent.total_bounds[1]],
                            [anti_maxx, wgs_extent.total_bounds[1]],
                            [anti_maxx, wgs_extent.total_bounds[3]],
                            [anti_minx, wgs_extent.total_bounds[3]],
                            [anti_minx, wgs_extent.total_bounds[1]]])

    wgs_anti_extent = gp.GeoDataFrame(index=[0], crs = "epsg:4326", geometry=[wgs_anti_poly])
    wgs_anti_extent.to_file("data/wgs_anti.gpkg", driver="GPKG")
    
    return wgs_anti_extent

def webmer_shift(wgs_anti_extent):
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

    webmer_anti_extent = gp.GeoDataFrame(index=[0], crs = "epsg:3857", geometry=[webmer_anti_poly])
    webmer_anti_extent.to_file("data/webmer.gpkg", driver="GPKG")
    
    return webmer_anti_extent 


if __name__ == "__main__":
    # World circumfrence in meters
    WORLD_CIRCUM = 2 * math.pi * 6378137

    in_file = sys.argv[1]
    
    main(in_file)