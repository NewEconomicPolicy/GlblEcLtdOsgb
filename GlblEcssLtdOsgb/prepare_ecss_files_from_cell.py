"""
#-------------------------------------------------------------------------------
# Name:        prepareEcosseFiles.py
# Purpose:
# Author:      s03mm5
# Created:     08/12/2015
# Copyright:   (c) s03mm5 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#
"""
__version__ = '1.0.00'
__prog__ = 'prepare_ecosse_files.py'

# Version history
# ---------------
#
from os.path import join, lexists, basename
from os import makedirs
from shutil import copyfile

from glbl_ecss_cmmn_funcs import write_kml_file, write_manifest_file, input_txt_line_layout, write_signature_file

sleepTime = 5
GRANULARITY = 120
ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

def make_ecss_files_from_cell(form, climgen, ltd_data, grid_cell):
    """
    generate sets of Ecosse files for each site
    where each site has one or more soils and each soil can have one or more dominant soils
    pettmp_grid_cell is climate data for this soil grid point
    """
    func_name = 'make_ecss_files_from_cell'

    area = 1
    lat = grid_cell.lat
    lon = grid_cell.lon
    mu_globals_props = grid_cell.mu_globals_props
    lta = grid_cell.lta
    province = grid_cell.grid_ref

    sims_dir = climgen.sims_dir
    fut_clim_scen = climgen.fut_clim_scen

    # write stanza for input.txt file consisting of long term average climate
    # =======================================================================
    hist_wthr_recs = []
    for imnth, month in enumerate(climgen.months):
        hist_wthr_recs.append(input_txt_line_layout('{}'.format(round(lta['precip'][imnth], 1)), \
                                            '{} long term average monthly precipitation [mm]'.format(month)))

    for imnth, month in enumerate(climgen.months):
        hist_wthr_recs.append(input_txt_line_layout('{}'.format(round(lta['tas'][imnth], 2)), \
                                            '{} long term average monthly temperature [degC]'.format(month)))

    #------------------------------------------------------------------
    # Create a set of simulation input files for each dominant
    # soil-land use type combination
    #------------------------------------------------------------------
    # construct directory name with all dominant soils

    for pair in mu_globals_props.items():
        mu_global, proportion = pair
        if mu_global in form.hwsd_mu_globals.bad_mu_globals:
            print(WARN_STR + 'No soil record for mu global: {}\tlat lon: {} {}'.format(mu_global,
                                                                                       round(lat, 5), round(lon, 5)))
            continue

        area_for_soil = area*proportion
        soil_list = form.hwsd_mu_globals.soil_recs[mu_global]

        for soil_num, soil in enumerate(soil_list):
            # identifer = grid_cell.grid_ref + '_mu{:0=5d}_s{:0=2d}'.format(mu_global, soil_num + 1)
            identifer = grid_cell.grid_ref + '_s{:0=2d}'.format(soil_num + 1)

            sim_dir = join(sims_dir, climgen.study, identifer)
            if not lexists(sim_dir):
                makedirs(sim_dir)

            ltd_data.write(sim_dir, soil, lat, hist_wthr_recs, grid_cell.met_rel_path)

            # write kml file if requested and signature file
            # ==============================================
            if form.sttngs['kml_flag'] and soil_num == 0:
                write_kml_file(sim_dir,  str(mu_global), mu_global, lat, lon)

            write_signature_file(sim_dir, mu_global, soil, lat, lon, province)

            # copy across Model_Switches.dat file
            # ===================================
            outMdlSwtchs = join(sim_dir, basename(form.default_model_switches))
            copyfile(form.default_model_switches, outMdlSwtchs)

        # manifest file is essential for subsequent processing
        # ====================================================
        write_manifest_file(form.study, fut_clim_scen, sim_dir, soil_list, mu_global, lat, lon, area_for_soil)

    # end of Soil loop
    # ================

    return
