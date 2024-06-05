#-------------------------------------------------------------------------------
# Name:        grid_cell_high_level_fns.py
# Purpose:     consist of high level functions invoked by main GUI
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
# Description:#
#-------------------------------------------------------------------------------
#
__prog__ = 'grid_cell_high_level_fns.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from os import makedirs
from os.path import isdir, join
from PyQt5.QtWidgets import QApplication

from hwsd_bil import HWSD_bil
from getClimGenNC import ClimGenNC
from getClimGenFns import check_clim_nc_limits
from getClimGenOsbgFns import fetch_chess_bbox_indices, open_chess_dsets, close_chess_dsets, add_data_to_grid_cells
from glbl_ecsse_high_level_fns import simplify_soil_recs
from make_ltd_data_files import MakeLtdDataFiles
from prepare_ecss_files_from_cell import make_ecss_files_from_cell

MASK_FLAG = False
snglPntFlag = True

def _generate_ecosse_files_for_cells(form, climgen, hwsd, grid_cells):
    """

    """
    # Initialise the limited data object with general settings that do not change between simulations
    # ===============================================================================================
    ltd_data = MakeLtdDataFiles(form, climgen, comments=True)  # create limited data object

    for grid_ref in grid_cells.keys():
        grid_cell = grid_cells[grid_ref]

        # extract required values from the HWSD database
        # ==============================================
        lon = float(grid_cell.lon)
        lat = float(grid_cell.lat)
        nvals_read = hwsd.read_bbox_mu_globals([lon, lat], snglPntFlag)

        # retrieve dictionary mu_globals and number of occurrences
        # ========================================================
        mu_globals = hwsd.get_mu_globals_dict()
        if mu_globals is None:
            print('No soil records for this area\n')
            continue

        # create and instantiate a new class NB this stanza enables single site
        # ==================================
        hwsd_mu_globals = type('test', (), {})()
        hwsd_mu_globals.soil_recs = hwsd.get_soil_recs(mu_globals)
        if len(mu_globals) == 0:
            print('No soil data for this area\n')
            continue

        grid_cell.mu_globals_props = {next(iter(mu_globals)): 1.0}

        mess = 'Cell {} has HWSD mu_global: {}'.format(grid_ref, list(grid_cell.mu_globals_props.keys())[0])
        form.lgr.info(mess); print(mess)
        QApplication.processEvents()

        make_ecss_files_from_cell(form, climgen, ltd_data, grid_cell)

    return

def generate_grid_cell_sims(form, grid_cells):
    """
    called from GUI
    """
    # weather choice
    # ==============
    wthr_rsrc = form.combo10w.currentText()
    if wthr_rsrc != 'CHESS':
        print('Weather resource must be CHESS')
        return

    if form.w_use_dom_soil.isChecked():
        dom_soil_flag = True
    else:
        dom_soil_flag = False

    # make sure bounding box is correctly set
    # =======================================
    lon_ll = float(form.w_ll_lon.text())
    lat_ll = float(form.w_ll_lat.text())
    lon_ur = float(form.w_ur_lon.text())
    lat_ur = float(form.w_ur_lat.text())
    form.sttngs['bbox'] =  list([lon_ll, lat_ll, lon_ur, lat_ur])

    # ==========
    chess_extent = fetch_chess_bbox_indices(lon_ll, lat_ll, lon_ur, lat_ur)

    # check requested AOI coordinates against extent of the weather resource dataset
    # ==============================================================================
    if check_clim_nc_limits(form, wthr_rsrc, form.sttngs['bbox']):
        print('Selected ' + wthr_rsrc)
        form.historic_wthr_flag = wthr_rsrc
        form.future_climate_flag   = wthr_rsrc
    else:
        return

    # ========
    hwsd = HWSD_bil(form.lgr, form.hwsd_dir)
    climgen = ClimGenNC(form)

    # TODO: patch to be sorted
    # ========================
    mu_global_pairs = {}
    for mu_global in form.hwsd_mu_globals.mu_global_list:
        mu_global_pairs[mu_global] = None

    soil_recs = hwsd.get_soil_recs(mu_global_pairs)  # list is already sorted with bad muglobals removed
    form.hwsd_mu_globals.soil_recs = simplify_soil_recs(soil_recs, dom_soil_flag)
    form.hwsd_mu_globals.bad_mu_globals = [0] + hwsd.bad_muglobals
    del (soil_recs)

    study = form.w_study.text()
    study_dir = join(form.sttngs['sims_dir'], study)
    if not isdir(study_dir):
        makedirs(study_dir)
    climgen.study = study
    climgen.study_dir = study_dir

    open_chess_dsets(climgen)

    add_data_to_grid_cells(climgen, grid_cells)

    _generate_ecosse_files_for_cells(form, climgen, hwsd, grid_cells)

    close_chess_dsets(climgen)

    return
