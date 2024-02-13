# anti-meridian-warp

Python method for warping GTiff in **NZTM** to **Web Mercator** across the anti-meridian.

Tested additonally warping from **EPSG:3994, EPSG 4167**

## Summary

A direct warp from NZTM to Web Mercator will split the file across the globe.  This method will create a non-split GTiff extending across the anti-meridian.

## Required

- docker
- make

## Basic Usage

Tested using NIWA 250m Bathymetry file from [Koordiates](https://koordinates.com/layer/8678-niwa-new-zealand-bathymetic-grid-2016/)

```
make anti-warp in_file=nzbathy_2016.tif
```
