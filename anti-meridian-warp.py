import rasterio as rio
import os
import geopandas as gp
from fiona.transform import transform_geom
from shapely.geometry import mapping, shape, box
import math
from osgeo import gdal
import sys

def main():    

    native_extent, in_crs, reso = get_native_extent()
    wgs_extent = repro_wgs(native_extent)
    anti_maxx, anti_minx = new_x_minmax(wgs_extent)
    wgs_anti_extent = wgs_poly(anti_minx, anti_maxx, wgs_extent)
    webmer_anti_extent = webmer_shift(wgs_anti_extent)
    
    # Reproject
    gdal.Warp(
        f"{DATA_DIR}/{os.path.basename(IN_FILE).split('.')[0]}-webmer.tif",
        IN_FILE,
        format = 'GTiff',
        outputBounds = (webmer_anti_extent.total_bounds[0],
                        webmer_anti_extent.total_bounds[1],
                        webmer_anti_extent.total_bounds[2],
                        webmer_anti_extent.total_bounds[3]),
        outputBoundsSRS = f'EPSG:{WEBMER}',
        srcSRS = in_crs,
        dstSRS = f'EPSG:{WEBMER}',
        xRes = reso[0], 
        yRes = reso[0], 
        callback=gdal.TermProgress_nocb
        )
    
def get_native_extent():   
    in_rio = rio.open(IN_FILE)
    in_crs = in_rio.crs
    reso = in_rio.res
    native_extent = gp.GeoDataFrame(index=[0], crs=in_crs, geometry=[box(*in_rio.bounds)])

    return native_extent, in_crs, reso

def repro_wgs(native_extent):
    wgs_poly = shape(
        transform_geom(
            src_crs=native_extent.crs.to_wkt(),
            dst_crs=f"epsg:{WGS}",
            geom=mapping(native_extent.geometry[0]),
            antimeridian_cutting=True,
        )
    )
    wgs_extent =  gp.GeoDataFrame(index=[0], crs=WGS, geometry=[wgs_poly])
    
    return wgs_extent

def new_x_minmax(wgs_extent):
    # Get new X Max from left poly
    wgs_multi_left = wgs_extent.explode(index_parts=True).iloc[0]
    wgs_edge_extent_left =  gp.GeoDataFrame(index=[0], crs=WGS, geometry=[wgs_multi_left.geometry])

    ## Shift left polygon around the globe using 360 degrees
    anti_maxx = wgs_edge_extent_left.total_bounds[2] + 360

    # Get new X Min from right poly
    wgs_multi_right = wgs_extent.explode(index_parts=True).iloc[1]
    wgs_edge_extent_right = gp.GeoDataFrame(index=[0], crs = WGS, geometry=[wgs_multi_right.geometry])
    anti_minx = wgs_edge_extent_right.total_bounds[0]
    
    return anti_maxx, anti_minx

def wgs_poly(anti_minx, anti_maxx, wgs_extent):
    wgs_anti_poly = box(anti_minx, wgs_extent.total_bounds[1], anti_maxx, wgs_extent.total_bounds[3])
    wgs_anti_extent = gp.GeoDataFrame(index=[0], crs=WGS, geometry=[wgs_anti_poly])
    
    return wgs_anti_extent

def webmer_shift(wgs_anti_extent):
    # Shift webmer poly over merdiain
    webmer_anti = wgs_anti_extent.to_crs(3857)

    shift_maxx = webmer_anti.total_bounds[0] + WORLD_CIRCUM
    shift_minx = webmer_anti.total_bounds[2]

    ## Build new Webmer Poly over Anti-Meridian
    webmer_anti_poly = box(shift_minx, webmer_anti.total_bounds[1], shift_maxx, webmer_anti.total_bounds[3])
    webmer_anti_extent = gp.GeoDataFrame(index=[0], crs=WEBMER, geometry=[webmer_anti_poly])
    
    return webmer_anti_extent 

if __name__ == "__main__":

    IN_FILE = sys.argv[1]    
    WORLD_CIRCUM = 2 * math.pi * 6378137 # World circumfrence in meters    
    DATA_DIR = 'data'
    WGS = 4326
    WEBMER = 3857
    
    main()