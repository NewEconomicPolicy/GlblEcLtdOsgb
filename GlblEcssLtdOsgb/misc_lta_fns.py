#-------------------------------------------------------------------------------
# Name:        misc_lta_fns.py
# Purpose:     dumping module
# Author:      Mike Martin
# Created:     31/07/2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

__prog__ = 'misc_lta_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from os.path import isdir, join, isfile
from time import strftime, sleep
from csv import writer

from cvrtcoord import OSGB36toWGS84, WGS84toOSGB36

OSGB_FNAME = 'coords_osgb'
WGS84_FNAME = 'coords_wgs84'
HANNAFRY_FN = 'coords_hannafry'
sleepTime = 5

def write_coords_check_file(log_dir, grid_cells):
    """

    """

    # string to uniquely identify output file
    # =======================================
    date_stamp = strftime('_%Y_%m_%d_%I_%M_%S')
    osgb_fn = join(log_dir, OSGB_FNAME + date_stamp + '.csv')
    osgb_fn = join(log_dir, OSGB_FNAME + '.csv')
    osgb_obj = open(osgb_fn, 'w', newline='')
    osgb_writer = writer(osgb_obj, delimiter=',')

    wgs84_fn = join(log_dir, WGS84_FNAME + date_stamp + '.csv')
    wgs84_fn = join(log_dir, WGS84_FNAME + '.csv')
    wgs84_obj = open(wgs84_fn, 'w', newline='')
    wgs84_writer = writer(wgs84_obj, delimiter=',')

    hfry_fn = join(log_dir, HANNAFRY_FN + '.csv')
    hfry_obj = open(hfry_fn, 'w', newline='')
    hfry_writer = writer(hfry_obj, delimiter=',')
    hfry_writer.writerow(['grid_ref', 'easting', 'nrthing', 'hf_lat', 'hf_lon', 'lat', 'lon', 'hf_esting', 'hf_nrthng'])

    for grid_ref in grid_cells.keys():
        grid_cell = grid_cells[grid_ref]

        lat, lon = grid_cell.lat, grid_cell.lon
        wgs84_writer.writerow([lat, lon, grid_ref])

        easting, nrthing = grid_cell.easting, grid_cell.nrthing
        osgb_writer.writerow([easting, nrthing, grid_ref])

        hf_esting, hf_nrthng = WGS84toOSGB36(lon, lat)
        hf_lon, hf_lat = OSGB36toWGS84(easting, nrthing)
        hfry_writer.writerow([grid_ref, easting, nrthing, hf_lat, hf_lon, lat, lon, hf_esting, hf_nrthng])

    osgb_obj.close()
    wgs84_obj.close()
    hfry_obj.close()

    return

"""
  # open LTA dataset
    # ================
    print('Opening long term average NetCDF file...')
    dataset_lta = Dataset(form.full_lta_nc_fname)
    vars_lta = dataset_lta.variables
    num_ncs_opened += 1    
    
    for metric in form.metrics:		# ['tas', 'pet', 'precip']
       grid_cell.lta[metric] = vars_lta[metric][:,indx_north,indx_east]
    
    # note float conversion from float32 otherwise rounding does not work as expected
        site.lta_pet = [round(float(pet), 1) for pet in grid_cell.lta['pet']]
        site.lta_precip = [round(float(precip), 1) for precip in grid_cell.lta['precip']]
        site.lta_tmean = [round(float(tmean), 1) for tmean in grid_cell.lta['tas']]
"""
