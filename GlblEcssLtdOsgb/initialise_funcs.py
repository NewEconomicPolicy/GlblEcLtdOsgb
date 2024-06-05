"""
#-------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""

__prog__ = 'initialise_funcs.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import exists, normpath, isfile, join, lexists, split, splitext
from os import getcwd, remove, makedirs, name as os_name
from json import load as json_load, dump as json_dump

from time import sleep
import sys

from glbl_ecss_cmmn_funcs import build_and_display_studies, check_sims_dir, check_lu_pi_json_fname
from glbl_ecss_cmmn_cmpntsGUI import print_resource_locations
from set_up_logging import set_up_logging
from hwsd_bil import check_hwsd_integrity
import hwsd_mu_globals_fns

from grid_cell_classes_fns import CropCalendar_1km
from plant_input_fns import check_plant_input_nc
from shape_funcs import format_bbox, calculate_area
from weather_datasets import change_wthr_rsrc, record_wthr_settings, read_wthr_dsets_detail
from mngmnt_fns_and_class import check_csv_coords_fname

WARN_STR = '*** Warning *** '
ERROR_STR = '*** Error *** '
BBOX_DEFAULT = [-4.8, 52.54, -3.42, 53.33] # lon_ll, lat_ll, lon_ur, lat_ur - Gwynedd, Wales
sleepTime = 5

SETTINGS_LIST = ['config_dir', 'csv_1km_fname', 'fname_png', 'hwsd_dir', 'hwsd_csv_fname', 'log_dir', 
                'lta_nc_fname', 'mask_fn', 'shp_dir', 'sims_dir', 'weather_dir']
LTA_NC_FNAME = 'lta_nc_fname'

MIN_GUI_LIST = ['weatherResource', 'aveWthrFlag', 'bbox', 'luPiJsonFname', 'piNcFname', 'usePiNcFname']
CMN_GUI_LIST = ['study', 'histStrtYr', 'histEndYr', 'climScnr', 'futStrtYr', 'futEndYr', 'eqilMode', 'runId',
                'n_coords', 'csvCoordsFname', 'realis']
# run modes
# =========
SPATIAL = 1
CSV_FILE = 2
RNDM_CELLS = 3
RUN_MODES = [SPATIAL, CSV_FILE, RNDM_CELLS]

def initiation(form):
    """
    this function is called to initiate the programme to process non-GUI settings.
    """
    glbl_ecsse_str = 'global_ecosse_config_hwsd_'
    fname_setup = 'glbl_ecss_setup_ver2_osgb.json'

    # retrieve settings
    # =================
    form.sttngs = _read_setup_file(form, fname_setup)
    form.sttngs['req_resol_upscale'] = 1

    form.sttngs['glbl_ecsse_str'] = glbl_ecsse_str
    config_files = build_and_display_studies(form, glbl_ecsse_str)
    if len(config_files) > 0:
        form.config_file = config_files[0]
    else:
        form.config_file = form.sttngs['config_dir'] + '/' + glbl_ecsse_str + 'dummy.txt'

    fname_model_switches = 'Model_Switches.dat'
    cwDir = getcwd()
    default_model_switches = join(cwDir, fname_model_switches)
    if isfile(default_model_switches):
        form.default_model_switches = default_model_switches
    else:
        print('{} file does not exist in directory {}'.format(fname_model_switches,cwDir))
        sleep(sleepTime)
        sys.exit(0)

    if not check_sims_dir(form.lgr, form.sims_dir):
        sleep(sleepTime)
        sys.exit(0)

    # create dump files for grid point with mu_global 0
    form.fobjs = {}
    output_fnames = list(['nodata_muglobal_cells_v2b.csv'])
    if form.zeros_file:
        output_fnames.append('zero_muglobal_cells_v2b.csv')
    for file_name in output_fnames:
        long_fname = join(form.sttngs['log_dir'], file_name)
        key = file_name.split('_')[0]
        if exists(long_fname):
            try:
                remove(long_fname)
            except (PermissionError) as e:
                mess = 'Failed to delete mu global zeros dump file: {}\n\t{} '.format(long_fname, e)
                print(mess + '\n\t- check that there are no other instances of GlblEcosse'.format(long_fname, e))
                sleep(sleepTime)
                sys.exit(0)

        form.fobjs[key] = open(long_fname,'w')

    return

def _read_setup_file(form, fname_setup):
    """
    read settings used for programme from the setup file, if it exists,
    or create setup file using default values if file does not exist
    """
    func_name =  __prog__ +  ' _read_setup_file'

    setup_file = join(getcwd(), fname_setup)
    if exists(setup_file):
        try:
            with open(setup_file, 'r') as fsetup:
                settings = json_load(fsetup)
        except (OSError, IOError) as e:
                sleep(sleepTime)
                exit(0)
    else:
        print(ERROR_STR + 'setup file ' + setup_file + ' must exist')
        sleep(sleepTime)
        exit(0)

    # initialise vars
    # ===============
    weather_dir, config_dir, log_dir, form.images_dir = 4*['']
    form.lu_pi_content = {}     # TODO

    # validate setup file
    # ===================
    grp = 'setup'    
    for key in SETTINGS_LIST:
        if key not in settings[grp]:
            print(ERROR_STR + 'setting {} is required in setup file {} '.format(key, setup_file))
            sleep(sleepTime)
            exit(0)

    config_dir = settings[grp]['config_dir']
    form.fname_png  = settings[grp]['fname_png']
    hwsd_dir        = settings[grp]['hwsd_dir']
    hwsd_csv_fname  = settings[grp]['hwsd_csv_fname']
    log_dir         = settings[grp]['log_dir']
    lta_nc_fname  = settings[grp]['lta_nc_fname']
    mask_fn = settings[grp]['mask_fn']
    form.shp_dir    = settings[grp]['shp_dir']
    sims_dir        = settings[grp]['sims_dir']
    wthr_dir     = settings[grp]['weather_dir']
    csv_1km_fname = settings[grp]['csv_1km_fname']

    # check directories exist for configuration and log files
    # ========================================================
    if not lexists(log_dir):
        makedirs(log_dir)

    # set up logging
    # ==============
    form.settings = {}
    form.settings['log_dir'] = log_dir
    set_up_logging(form, 'global_ecosse_min')

    if not lexists(config_dir):
        makedirs(config_dir)

    # ==============
    if isfile(hwsd_csv_fname):
        # read CSV file using pandas and create obj
        # =========================================
        form.hwsd_mu_globals = hwsd_mu_globals_fns.HWSD_mu_globals_csv(form, hwsd_csv_fname)
        print(form.hwsd_mu_globals.aoi_label)
    else:
        print(ERROR_STR + 'HWSD csv file ' + hwsd_csv_fname + ' must exist')
        sleep(sleepTime)
        exit(0)

    # ======= LTA ========
    if isfile(lta_nc_fname):
       print('\nWill use LTA (long term average) weather file: ' + lta_nc_fname)
    else:
       print(ERROR_STR + 'LTA NC file ' + lta_nc_fname + ' must exist')
       sleep(sleepTime)
       exit(0)

    # grid file with sowing dates
    # ===========================
    if isfile(csv_1km_fname):
        print('\nWill use grid definition file: ' + csv_1km_fname)

        # retrieve grid cell definitions
        # ==============================
        crop_grid = CropCalendar_1km(form.lgr, csv_1km_fname)
        if crop_grid.nlines is None:
            print('Crop grid creation failed')
            return []

        form.crop_grid = crop_grid
    else:
        settings[grp]['csv_1km_fname'] = None
        form.crop_grid = None
        print('Grid definition file {} does not exist'.format(csv_1km_fname))

    # ==============
    if isfile(mask_fn):
        form.mask_fn = mask_fn
    else:
        if mask_fn != '':
            print(WARN_STR + 'Land use mask file ' + mask_fn + ' does not exist')
        form.mask_fn = None

    # additional settings to enable ECOSSE to be run
    # ==============================================
    form.runsites_py = None
    form.python_exe = None
    form.runsites_config_file = None
    run_ecosse_flag = False
    if 'python_exe' in settings[grp].keys() and 'runsites_py' in settings[grp].keys():
        runsites_py = settings[grp]['runsites_py']
        python_exe = settings[grp]['python_exe']

        # check that the runsites configuration file exists
        # =================================================
        runsites_config_file = join(config_dir,'global_ecosse_ltd_data_runsites_config.json')
        mess = '\nRun sites configuration file: ' + runsites_config_file

        if isfile(runsites_config_file) and isfile(runsites_py) and isfile(python_exe):

            mess += ' exists\nRun sites script: ' + runsites_py + ' exists'
            form.runsites_py = runsites_py
            form.python_exe = python_exe
            form.runsites_config_file = runsites_config_file
            run_ecosse_flag = True
        else:
            mess += '\n\tor ' + python_exe + '\n\tor ' + runsites_py + ' do not exist - cannot run ECOSSE'
            form.runsites_config_file = None

        print(mess)
    else:
        print(WARN_STR + 'attributes python_exe or runsites_py not present in setup file, cannot run ECOSSE' + '\n')

    if run_ecosse_flag:
        # ascertain which version of Ecosse is defined in the runsites file
        # =================================================================
        if type(runsites_config_file) is str:
            with open(runsites_config_file, 'r') as fconfig:
                config = json_load(fconfig)
                # print('Read config file ' + runsites_config_file)
        try:
            fn = split(config['Simulations']['exepath'])[1]
        except KeyError as err:
            print(WARN_STR + 'could not identify Ecosse version in run sites file: ' + runsites_config_file + '\n')
        else:
            settings['setup']['ecosse_exe'] = splitext(fn)[0].lower()
    else:
        settings['setup']['ecosse_exe'] = None

        # HWSD is crucial
    # ===============
    if lexists(hwsd_dir):
        check_hwsd_integrity(settings[grp]['hwsd_dir'])
        form.hwsd_dir = hwsd_dir
    else:
        print('Error reading {}\tHWSD directory {} must exist'.format(setup_file, hwsd_dir))
        sleep(sleepTime)
        exit(0)

    # weather is crucial
    # ===================
    if lexists(wthr_dir):
        form.wthr_dir = wthr_dir
        form.settings['weather_dir'] = wthr_dir
    else:
        print('Error reading {}\tClimate directory {} must exist'.format(setup_file, wthr_dir))
        sleep(sleepTime)
        exit(0)

    # sims dir checked later
    # ======================
    form.sims_dir = sims_dir

    # check weather data
    # ==================
    if form.version == 'HWSD_grid':
       rqurd_wthr_rsrcs = ['CRU', 'CHESS']  # required weather resources
    else:
       rqurd_wthr_rsrcs = ['CRU', 'EObs', 'HARMONIE']

    form.wthr_settings_prev = {}
    read_wthr_dsets_detail(form, rqurd_wthr_rsrcs)

    # TODO: most of these are not used
    # ================================
    grp = 'run_settings'
    try:
        settings['setup']['completed_max'] = settings[grp]['completed_max']
        settings['setup']['start_at_band'] = settings[grp]['start_at_band']
        space_remaining_limit = settings[grp]['space_remaining_limit']
        settings['setup']['kml_flag'] = settings[grp]['kml_flag']
        form.soilTestFlag = settings[grp]['soil_test_flag']
        form.zeros_file   = settings[grp]['zeros_file']
    except KeyError:
        print('{}\tError in group: {}'.format(func_name, grp))
        sleep(sleepTime)
        exit(0)

    print_resource_locations(setup_file, config_dir, hwsd_dir, wthr_dir, lta_nc_fname, sims_dir, log_dir)

    return settings['setup']

def read_config_file(form):
    """
    read widget settings used in the previous programme session from the config file, if it exists,
    or create config file using default settings if config file does not exist
    """
    func_name =  __prog__ +  ' read_config_file'

    config_file = form.config_file
    if exists(config_file):
        try:
            with open(config_file, 'r') as fconfig:
                config = json_load(fconfig)
                print('Read config file ' + config_file)
        except (OSError, IOError) as err:
                print(err)
                return False
    else:
        config = _write_default_config_file(config_file)

    grp = 'minGUI'
    for key in MIN_GUI_LIST:
        if key not in config[grp]:
            print(ERROR_STR + 'setting {} is required in configuration file {} '.format(key, config_file))
            form.sttngs['bbox'] = BBOX_DEFAULT
            form.csv_fname = ''
            return False

    # added July 2020 to enable MK plant inputs NC file
    # =================================================
    if config[grp]['usePiNcFname']:
        form.w_use_pi_nc.setCheckState(2)
    else:
        form.w_use_pi_nc.setCheckState(0)

    pi_nc_fname = config[grp]['piNcFname']
    form.w_lbl_pi_nc.setText(pi_nc_fname)
    check_plant_input_nc(form, pi_nc_fname)

    # ==== end of MK plant inputs NC file extension =====

    wthr_rsrc = config[grp]['weatherResource']
    ave_wthr = config[grp]['aveWthrFlag']
    form.sttngs['bbox'] = config[grp]['bbox']
    lu_pi_json_fname = config[grp]['luPiJsonFname']

    form.combo10w.setCurrentText(wthr_rsrc)
    change_wthr_rsrc(form, wthr_rsrc)

    # land use and plant input
    # ========================
    form.w_lbl13.setText(lu_pi_json_fname)
    form.w_lbl14.setText(check_lu_pi_json_fname(form))  # displays file info

    # common area
    # ===========
    grp = 'cmnGUI'
    for key in CMN_GUI_LIST:
        if key not in config[grp]:
            if key == 'realis':
                config[grp]['realis'] = '01'
            else:
                print(ERROR_STR + 'in group: {} - setting {} is required in config file {}'.format(grp, key, config_file))
                return False

    form.w_study.setText(str(config[grp]['study']))
    hist_strt_year = config[grp]['histStrtYr']
    hist_end_year  = config[grp]['histEndYr']
    scenario       = config[grp]['climScnr']
    realis = config[grp]['realis']
    sim_strt_year  = config[grp]['futStrtYr']
    sim_end_year   = config[grp]['futEndYr']
    form.w_equimode.setText(str(config[grp]['eqilMode']))

    run_id = config[grp]['runId']
    w_button = form.w_inpt_choice.button(run_id)
    w_button.setChecked(True)

    form.w_ncoords.setText(config[grp]['n_coords'])

    csv_fn = config[grp]['csvCoordsFname']
    form.w_lbl20.setText(csv_fn)
    check_csv_coords_fname(csv_fn, form.w_lbl21)

    # record weather settings
    # =======================
    form.wthr_settings_prev[wthr_rsrc] = record_wthr_settings(scenario, hist_strt_year, hist_end_year,
                                                                     sim_strt_year, sim_end_year)
    form.combo09s.setCurrentText(hist_strt_year)
    form.combo09e.setCurrentText(hist_end_year)
    form.combo10s.setCurrentText(scenario)
    form.combo10r.setCurrentText(realis)
    form.combo11s.setCurrentText(sim_strt_year)
    form.combo11e.setCurrentText(sim_end_year)

    # ===================
    # bounding box set up
    # ===================
    area = calculate_area(form.sttngs['bbox'])
    ll_lon, ll_lat, ur_lon, ur_lat = form.sttngs['bbox']
    form.w_ur_lon.setText(str(ur_lon))
    form.w_ur_lat.setText(str(ur_lat))
    form.fstudy = ''
    form.w_ll_lon.setText(str(ll_lon))
    form.w_ll_lat.setText(str(ll_lat))
    form.w_bbox.setText(format_bbox(form.sttngs['bbox'],area))

    # set check boxes
    # ===============
    if ave_wthr:
        form.w_ave_wthr.setCheckState(2)
    else:
        form.w_ave_wthr.setCheckState(0)

    # avoids errors when exiting
    # ==========================
    form.req_resol_deg = None
    form.req_resol_granul = None
    form.w_use_dom_soil.setChecked(True)
    form.w_use_high_cover.setChecked(True)

    if form.python_exe == '' or form.runsites_py == '' or form.runsites_config_file is None:
        print('Could not activate Run Ecosse widget - python: {}\trunsites: {}\trunsites_config_file: {}'
                                                .format(form.python_exe, form.runsites_py, form.runsites_config_file))
        form.w_run_ecosse.setEnabled(False)
        form.w_auto_spec.setEnabled(False)

    return True

def write_config_file(form, message_flag = True):
    """
    write current selections to config file
    """
    study = form.w_study.text()

    # facilitate multiple config file choices
    # =======================================
    glbl_ecsse_str = form.sttngs['glbl_ecsse_str']
    config_file = join(form.sttngs['config_dir'], glbl_ecsse_str + study + '.json')

    # prepare the bounding box
    # ========================
    ll_lon = 0.0
    ll_lat = 0.0
    try:
        ll_lon = float(form.w_ll_lon.text())
        ll_lat = float(form.w_ll_lat.text())
        ur_lon = float(form.w_ur_lon.text())
        ur_lat = float(form.w_ur_lat.text())
    except ValueError as err:
        print('Problem writing bounding box to config file: ' + str(err))
        ur_lon = 0.0
        ur_lat = 0.0
    form.sttngs['bbox'] = list([ll_lon,ll_lat,ur_lon,ur_lat])

    # TODO: might want to consider where else in the work flow to save these settings
    wthr_rsrc = form.combo10w.currentText()
    realis = form.combo10r.currentText()
    scenario = form.combo10s.currentText()
    hist_strt_year   = form.combo09s.currentText()
    hist_end_year    = form.combo09e.currentText()
    sim_strt_year    = form.combo11s.currentText()
    sim_end_year     = form.combo11e.currentText()
    form.wthr_settings_prev[wthr_rsrc] = record_wthr_settings(scenario, hist_strt_year, hist_end_year,
                                                                     sim_strt_year, sim_end_year)

    config = {
        'minGUI': {
            'bbox'            : form.sttngs['bbox'],
            'snglPntFlag'     : False,
            'weatherResource' : wthr_rsrc,
            'aveWthrFlag'  : form.w_ave_wthr.isChecked(),
            'luPiJsonFname': form.w_lbl13.text(),
            'piNcFname'    : form.w_lbl_pi_nc.text(),
            'usePiNcFname' : form.w_use_pi_nc.isChecked(),
            'usePolyFlag'  : False
        },
        'cmnGUI': {
            'study'     : form.w_study.text(),
            'histStrtYr': hist_strt_year,
            'histEndYr' : hist_end_year,
            'climScnr'  : scenario,
            'futStrtYr' : sim_strt_year,
            'futEndYr'  : sim_end_year,
            'eqilMode'  : form.w_equimode.text(),
            'realis': realis,
            'runId'     : form.w_inpt_choice.checkedId(),
            'n_coords'  : form.w_ncoords.text(),
            'csvCoordsFname': form.w_lbl20.text()
            }
        }
    if isfile(config_file):
        descriptor = 'Overwrote existing'
    else:
        descriptor = 'Wrote new'
    if study != '':
        with open(config_file, 'w') as fconfig:
            json_dump(config, fconfig, indent=2, sort_keys=True)
            if message_flag:
                print('\n' + descriptor + ' configuration file ' + config_file)
            else:
                print()
    return

def write_runsites_config_file(form):

    func_name =  __prog__ +  ' write_runsites_config_file'

    # read the runsites config file and edit one line
    # ======================================
    runsites_config_file = form.runsites_config_file
    try:
        with open(runsites_config_file, 'r') as fconfig:
            config = json_load(fconfig)
            print('Read config file ' + runsites_config_file)
    except (OSError, IOError) as err:
            print(err)
            return False

    # overwrite config file
    # =====================
    if hasattr(form, 'w_study'):
        sims_dir = normpath(join(form.sims_dir, form.w_study.text()))
    else:
        sims_dir = normpath(join(form.sims_dir, form.study))

    config['Simulations']['sims_dir'] = sims_dir
    with open(runsites_config_file, 'w') as fconfig:
        json_dump(config, fconfig, indent=2, sort_keys=True)
        print('Edited ' + runsites_config_file + ' with simulation location: ' + sims_dir)

    return True

def _write_default_config_file(config_file):
    """
    stanza if config_file needs to be created
    """
    _default_config = {
        'minGUI': {
            'aveWthrFlag': False,
            'bbox': BBOX_DEFAULT,
            'cordexFlag': 0,
            'hwsdCsvFname': '',
            'luPiJsonFname': '',
            'snglPntFlag': True,
            'usePolyFlag': False
        },
        'cmnGUI': {
            'climScnr' : 'rcp26',
            'eqilMode' : '9.5',
            'futStrtYr': '2006',
            'futEndYr' : '2015',
            'histStrtYr': '1980',
            'histEndYr' : '2005',
            'study'    : ''
        }
    }
    # if config file does not exist then create it...
    with open(config_file, 'w') as fconfig:
        json_dump(_default_config, fconfig, indent=2, sort_keys=True)
        fconfig.close()
        return _default_config
