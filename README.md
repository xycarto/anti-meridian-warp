# anti-meridian-warp

Python method for warping GTiff in NZTM to Webmercator across the anti-meridian.

This is intentionally verbose to help keep track of what is happening.

The intetion of this is to demonstrate one method to get across the anti-meridian when warping. Ideally, someone will take this and make it better for their own process.  

The interum step of reprojecting into WGS84, before getting to Webmercator, may be unnecessary.

## Summary

A direct warp from NZTM to Webmercator will split the file across the globe.  This method will find the extent to warp to in Webmercator across the anti-meridian and warp the file to that extent, creating a non-split GTiff extending across the anti-meridian.

This method can be done in any number of different processes. This is merely one method to warp a GTiff across the anti-meridian.

## Required

- python
- geopandas
- fiona
- rasterio
- gdal

## Basic Steps

1. Find extent of input file
2. Reproject this extent to WGS 84 using `fiona` with `antimeridian_cutting=True`. This creates a multi-polygon to get across the anti-meridian.
3. Find extent of each multi-poly
4. Shift left polygon over anti-merdian, next to right polygon
5. Build extent of polygons combined
6. Reproject WGS polygon to Webmercator
7. Shift maxx of Webmercator polygon across the anti-meridian
8. Find extent of new Webmercator polygon
9. Use new extent as output bounds in `gdal.Warp` process
