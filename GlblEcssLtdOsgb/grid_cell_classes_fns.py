#-------------------------------------------------------------------------------
# Name:        grid_cell_classes_fns.py
# Purpose:     Class to read crop_calendar_1km.csv
#
# Author:      Mike Martin
# Created:     05/08/2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

__prog__ = 'crop_grid_functions'
__version__ = '0.0.0'
__author__ = 'mmartin'

#
from PyQt5.QtWidgets import QApplication
from time import time
from os.path import isfile
from locale import setlocale, LC_ALL, format_string
from random import randint
from csv import reader, Sniffer
from pandas import read_csv
from netCDF4 import Dataset

from cvrtcoord import WGS84toOSGB36, OSGB36toWGS84
from misc_lta_fns import write_coords_check_file

METRICS = ['precip', 'tas']

setlocale(LC_ALL, '')
sleepTime = 2
NoData = -999.0
numDaysToCheck  = 25   # validate this number of days before accepting a point

CSV_FILE = 2
MORECS_DFLT = 1  # TODO

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

def generate_osgb_sites(form, run_id):
    """

    """
    if run_id == CSV_FILE:
        csv_coords_fn = form.w_lbl20.text()
        if not isfile(csv_coords_fn):
            print(WARN_STR + csv_coords_fn + ' does not exist')
            return
    else:
        try:
            num_cells = int(form.w_ncoords.text())
        except ValueError as err:
            print(err)
            return

    metric = 'precip'
    nc_fname = form.wthr_sets['CHESS_historic']['ds_' + metric]
    nc_dset = Dataset(nc_fname)

    if run_id == CSV_FILE:
        grid_cells = fetch_cells_from_csv(form, nc_dset.variables, metric, csv_coords_fn)
        if grid_cells is None:
            print('No grid cells returned from ' + csv_coords_fn)
    else:
        grid_cells = fetch_random_cells(form, nc_dset.variables, metric, num_cells)

    nc_dset.close()

    if grid_cells is not None:
        nsites = len(grid_cells)
        if nsites == 0:
            print('No sites available')
        else:
            print('Generated {} grid cells '.format(nsites))
            write_coords_check_file(form.sttngs['log_dir'], grid_cells)

    return grid_cells

def fetch_cells_from_csv(form, vars_wthr, metric, csv_fn):
    """
    read and validate CSV file of weather
    could use Multiple Char Separator in read_csv in Pandas
           see: https://datascientyst.com/use-multiple-char-separator-read_csv-pandas/

    Met Office Rainfall and Evapo-transpiration Calculation System (MORECS) – for modelling soil moisture and runoff
                            see: https://www.metoffice.gov.uk/services/business-industry/agriculture
    """
    func_name =  __prog__ + '  fetch_cells_from_csv'

    # =====================
    with open(csv_fn, 'r') as fobj:
        dialect = Sniffer().sniff(fobj.readline(), [',','\t'])
    delim = dialect.delimiter  # "delimiter" is a 1-character string

    # columns are: MORECS_ID,Grid_Easting,Grid_Northing,PLAN_NO_1km_ID
    # ================================================================
    coords = {'site_code': [], 'easting': [], 'nrthing': [], 'grid_ref': []}
    csv_df = read_csv(csv_fn, sep = delim)
    if 'BNG_X' not in csv_df.columns or 'BNG_Y' not in csv_df.columns:
        print(ERROR_STR + 'Invalid CSV file ' + csv_fn + ' - columns BNG_X and BNG_Y must be present')
        return None

    coords['easting'] = list(csv_df['BNG_X'])
    coords['nrthing'] = list(csv_df['BNG_Y'])
    coords['site_code'] = list(csv_df['site_code'])

    ncrds_read = len(coords['easting'])
    if ncrds_read == 0:
        return None

    coords['grid_ref'] = ncrds_read*[None]

    # =====================
    osgb_df = form.crop_grid.df
    grid_cells = {}
    nvalid_cells = 0
    duplics_list = []
    not_found_cells = 0
    no_east_cells = 0
    nbad_cells = 0
    last_time = time()
    for site_code, easting, nrthing, grid_ref in zip(coords['site_code'], coords['easting'], coords['nrthing'], coords['grid_ref']):
        QApplication.processEvents()
        res = osgb_df.loc[(osgb_df['Grid_Easting'] == easting) & (osgb_df['Grid_Northing'] == nrthing)]
        if len(res) > 0:
            grid_ref = res['PLAN_NO_1km_ID'].values[0]
        else:
            print(WARN_STR + 'Easting {} and Northing: {} not found in OSGB lookup file'.format(easting, nrthing))
            not_found_cells += 1
            continue

        grid_cell = GridCell([MORECS_DFLT, easting, nrthing, grid_ref])
        if grid_cell.easting is None:
            no_east_cells += 1
            continue

        return_flag, grid_ref = check_grid_cell(form.lgr, vars_wthr, metric, site_code, grid_cell)
        if return_flag:
            if grid_ref in grid_cells:
                duplics_list.append([site_code, grid_ref, easting, nrthing, grid_cells[grid_ref].site_code])
            else:
                grid_cells[grid_ref] = grid_cell
                nvalid_cells += 1
        else:
            nbad_cells += 1

        new_time = time()
        if new_time - last_time > sleepTime:
            last_time = new_time
            print('\rNumber of valid cells: {}\trejected: {}'.format(nvalid_cells, nbad_cells))

    # report progress and exit
    # ========================
    mess =('Retrieved {} valid cells\t{} no data\t{} not found\t{} no easting\t{} duplicates'
                                .format(nvalid_cells, nbad_cells, not_found_cells, no_east_cells, len(duplics_list)))
    form.lgr.info(mess + 'in function ' + func_name)
    print('\n' + mess)

    return grid_cells

def fetch_random_cells(form, vars_wthr, metric, nrequested_cells):
    """

    """
    func_name =  __prog__ + '  fetch_random_cells'

    grid_cells = {}
    nvalid_cells = 0
    nbad_cells = 0
    last_time = time()
    while nvalid_cells < nrequested_cells:
        irec = randint(0, form.crop_grid.nlines)
        grid_cell = GridCell(form.crop_grid.df.values[irec])
        site_code = 'RND' + '{:0=3d}'.format(nvalid_cells + 1)
        return_flag, grid_ref = check_grid_cell(form.lgr, vars_wthr, metric, site_code, grid_cell)
        if return_flag:
            grid_cells[grid_ref] = grid_cell
            nvalid_cells += 1
        else:
            nbad_cells += 1

        new_time = time()
        if new_time - last_time > sleepTime:
            last_time = new_time
            print('\rNumber of valid cells: {}\trejected: {}'.format(nvalid_cells, nbad_cells))
            QApplication.processEvents()

    # report progress and exit
    # ========================
    mess =('Retrieved {} randomly selected cells\trejected {} cells with no data'.format(nvalid_cells, nbad_cells))
    form.lgr.info(mess + 'in function ' + func_name)
    print('\n' + mess)
    QApplication.processEvents()

    return grid_cells

def check_grid_cell(lggr, vars_wthr, metric, site_code, grid_cell):
    '''
    Check if looks like there is a complete set of data for this grid coordinate
    '''
    func_name = __prog__ +  ' check_nc_data'

    # easting and northing size in metres
    # ===================================
    easting    = grid_cell.easting
    nrthing   = grid_cell.nrthing
    gridsize   = abs((vars_wthr['x'][0] - vars_wthr['x'][1]))
    min_easting  = vars_wthr['x'][0] - (gridsize / 2.0)
    min_nrthing = vars_wthr['y'][0] - (gridsize / 2.0)

    # limit number of days to check to improve performance
    # ====================================================
    valid_flag = True
    ix_indx = int((easting - min_easting)/gridsize)
    iy_indx = int((nrthing - min_nrthing)/gridsize)

    grid_cell.indx_east = ix_indx
    grid_cell.indx_nrth = iy_indx

    lon, lat = OSGB36toWGS84(easting, nrthing)
    mess = '{} data for easting {}\t northing {}'.format(metric, easting, nrthing)
    mess += '\tat lon {}\tlat {}\tfunction {}'.format(round(float(lon), 5), round(float(lat), 5), func_name)

    grid_cell.lon = lon
    grid_cell.lat = lat
    grid_cell.site_code = site_code

    val_list = []
    for iday_indx in range(0, numDaysToCheck):
        try:
            val = vars_wthr[metric][iday_indx][iy_indx][ix_indx]
        except (IndexError, RuntimeError) as err:
            lggr.info(ERROR_STR + ' {}\tiday_indx {}\tiy_indx {}\tix_indx {}'.format(err, iday_indx, iy_indx, ix_indx))
            valid_flag = False
            break

        if hasattr(val, '_mask'):
            lggr.info('No ' + mess)
            valid_flag = False
            break
        else:
            val_list.append(val)

    if valid_flag:
        lggr.info('Good ' + mess)

    return list([valid_flag, grid_cell.grid_ref])

class CropCalendar_1km(object,):

    def __init__(self, lggr, csv_1km_fname):
        """
        read and validate the CSV file consisting of MORECS data
        see:
            Meteorological Office Rainfall and Evaporation Calculation System (version 2.0)
            https://catalogue.ceh.ac.uk/documents/b9155463-ac86-4e19-a24f-57cef6b79505
        """
        nlines, df = 2*[None]

        if isfile(csv_1km_fname):
            try:
                df = read_csv(csv_1km_fname, sep = ',', usecols = range(4))
            except ValueError as err:
                mess = ERROR_STR + '{}: {}'.format(err, csv_1km_fname)
            else:
                nlines = len(df.values)
                mess = 'read ' + format_string("%d", nlines, grouping=True) + ' lines using pandas'
        else:
            mess = ERROR_STR + 'File ' + csv_1km_fname + ' is not a regular file'

        self.nlines = nlines
        self.df = df
        print(mess)
        lggr.info(mess)

class GridCell(object,):

    def __init__(self, grid_cell):
        """
        TODO: validate grid_cell
        """
        func_name = ' GridCell __init__'

        if len(grid_cell) < 4:
            print(WARN_STR + 'creating GridCell object, input list must have a minimum length of 4')
            self.morecs_id = None
            self.easting = None
            self.nrthing = None
            self.grid_ref = None
        else:
            self.morecs_id = grid_cell[0]
            self.easting  = int(grid_cell[1])
            self.nrthing = int(grid_cell[2])
            self.grid_ref = grid_cell[3]

        self.indx_east = None
        self.indx_nrth = None
        self.lat = None
        self.lon = None
        self.harvest = None # grid_cell[4:-2]

        # map a default value of None to each of the weather, LTA and soil dictionary keys to represent the absence of
        # a value which will later be assigned arrays
        #
        self.wthr = {}; self.lta = {}; self.soil = {}
        for metric in METRICS:
            self.wthr[metric] = None
            self.lta[metric] = None
'''
  for property in form.soil_properties:
            self.soil[property] = None
'''

