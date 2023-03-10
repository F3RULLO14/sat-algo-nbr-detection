import os
import argparse

import numpy as np
from numpy import ndarray

from osgeo import gdal
import rasterio as rio


def __get_band(fn:str, band:int = 1):
    """Extract a band to ndarray of given GeoTiff.

    Args:
        fn (str): GeoTiff location.
        band (int, optional): The band to extract. Defaults to 1.

    Returns:
        ndarray: A numpy array of the band extracting.
    """
    ds = gdal.Open(fn, gdal.GA_ReadOnly)
    return ds.GetRasterBand(band).ReadAsArray().astype('f4')


def __write(fn, arr, trans, crs:str = 'EPSG:4326', nodata:int = -1):
    """Write ndarray to GeoTiff.

    Args:
        fn (str): Output filename.
        arr (ndarray): Data to write to output.
        trans (object): Trasnform to write to output.
        crs (str, optional): The projection related to transform, desired for output. Defaults to 'EPSG:4326'.
        nodata (int, optional): Value indicating no data for a coordinate in output. Defaults to -1.
    """
    try:
        if os.path.exists(fn):
            os.remove(fn)
            
        r_dataset = rio.open(fn, 'w', driver='GTiff',
                        height=arr.shape[0],
                        width=arr.shape[1],
                        nodata=nodata,
                        count=1,
                        dtype=str(arr.dtype),
                        crs={'init': crs},
                        transform=trans)

        r_dataset.write(arr, 1)
        r_dataset.close()
    except Exception as e:
        print('Unable to write data to GeoTiff!')
        print(e)


def evaluate_band_burn_ratio(arr_nir :ndarray, arr_swir: ndarray):
    """Calculate the Normalized Burn Ratio of a given GeoTiff's NIR and SWIR bands.

    Args:
        arr_nir (NIR): Band as numpy array
        arr_swir (SWIR): Band as numpy array

    Returns:
        ndarray: An array of burn ratio values.
    """
    arr_nir_clamped = np.where(arr_nir < 0, 0, arr_nir)
    arr_swir_clamped = np.where(arr_swir < 0, 0, arr_swir)
    arr_nbr = np.divide(np.subtract(arr_nir_clamped, arr_swir_clamped), np.add(arr_nir_clamped, arr_swir_clamped))
    return np.nan_to_num(arr_nbr, nan=-9999)


def evaluate_cog_burn_ratio(fn_cog:str, fn_out:str = None):
    """Calculate the Normalized Burn Ratio of a COG and export the results to a new GeoTiff.

    Args:
        fn_cog (str): Cloud Optimized GeoTiff name.
        fn_out (str, optional): Output file ending in .tif. Defaults to None.

    Returns:
        ndarray, transform, crs: Data used to write a new tif
    """
    fn_nir = '{}.B8A.tif'.format(fn_cog) #'sample/HLS.S30.T11SKD.2022286T184329.v2.0.B8A.tif'
    fn_swir = '{}.B12.tif'.format(fn_cog) #'sample/HLS.S30.T11SKD.2022286T184329.v2.0.B12.tif'
    
    arr_nir = __get_band(fn_nir)
    arr_swir = __get_band(fn_swir)
    arr_nbr = evaluate_band_burn_ratio(arr_nir, arr_swir)
    
    with rio.open(fn_nir) as src:
        original_crs = str(src.crs)
        original_transform = src.transform
    
    if fn_out is not None:
        __write(fn_out, arr_nbr, original_transform, crs=original_crs, nodata=-9999)
        
    return arr_nbr, original_transform, original_crs
    
    
def evaluate_cog_burn_ratio_difference(fn_cog_before:str, fn_cog_after:str, fn_out:str):
    """Calculates the difference between two COGs' NBR values.

    Args:
        fn_cog_before (str): Pre fire COG.
        fn_cog_after (str): Post fire COG.
        fn_out (str): Output filename.
    """
    arr_before, trans_before, crs_before = evaluate_cog_burn_ratio(fn_cog_before)
    arr_after, trans_after, crs_after = evaluate_cog_burn_ratio(fn_cog_after)
    
    arr_mask = np.where((arr_before != -9999) & (arr_after != -9999), 1, 0)
    arr_dif = np.subtract(arr_before, arr_after).astype('f4')
    arr_dif_masked = np.where(arr_mask == 1, arr_dif, -9999)
    
    __write(fn_out, arr_dif_masked, trans_before, crs=crs_before, nodata=-9999)


if __name__ == '__main__':
    print('Started program.')
    
    print('Reading arguments...')
    parser = argparse.ArgumentParser(prog='NormalizedBurnRatio')
    parser.add_argument('fn_cog')
    parser.add_argument('fn_out')
    args = parser.parse_args()
    
    # good sample to determine difference in area, pre/post fire
    # before HLS.S30.T10SFJ.2022239T184919.v2.0
    # after HLS.S30.T10SFJ.2022314T185621.v2.0
    # evaluate_cog_burn_ratio_difference('sample/HLS.S30.T10SFJ.2022239T184919.v2.0', 'sample/HLS.S30.T10SFJ.2022314T185621.v2.0', 'output/burn_dif.tif')
    
    fn_cog = args.fn_cog #'sample/HLS.S30.T11SKD.2022286T184329.v2.0'
    fn_out = args.fn_out #'output/output.tif'
    evaluate_cog_burn_ratio(fn_cog, fn_out)
    print('Complete!')
