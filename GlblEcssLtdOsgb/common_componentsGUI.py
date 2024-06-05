"""
#-------------------------------------------------------------------------------
# Name:        common_componentsGUI.p
# Purpose:     consist of high level functions invoked by main GUI
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#
"""

__prog__ = 'common_componentsGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

# Version history
# ---------------
#
from os.path import normpath, isfile

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox, QRadioButton, QButtonGroup

from initialise_funcs import read_config_file, write_config_file
from glbl_ecss_cmmn_funcs import write_study_definition_file

WDGT_SIZE_40 = 40
WDGT_SIZE_60 = 60
WDGT_SIZE_100 = 100

EQUIMODE_DFLT = '6'     # default equilibrium mode

LU_DEFNS = {'lu_type' : ['Arable','Forestry','Miscanthus','Grassland','Semi-natural', 'SRC', 'Rapeseed', 'Sugar cane'],
                   'abbrev': ['ara',   'for',      'mis',      'gra',      'nat',     'src', 'rps',      'sgc'],
                        'ilu':[1,        3,          5,          2,          4,          6,     7,          7]}
# run modes
# =========
SPATIAL = 1
CSV_FILE = 2
RNDM_CELLS = 3

# ====================================
def input_choices(form, grid, irow):
    """
    
    """
    irow += 1
    w_lbl06b = QLabel('Run choices:')
    w_lbl06b.setAlignment(Qt.AlignRight)
    grid.addWidget(w_lbl06b, irow, 0)

    w_use_spatial = QRadioButton('Spatial')
    helpText = 'Use the 30 meter resolution iSDAsoil mapping system for Africa'
    helpText += ' - see: https://www.isda-africa.com/isdasoil/'
    w_use_spatial.setToolTip(helpText)
    w_use_spatial.setEnabled(False)
    grid.addWidget(w_use_spatial, irow, 1)
    form.w_use_spatial = w_use_spatial

    w_use_csv = QRadioButton('CSV file')
    helpText_csv = 'Use a comma Separated Values (CSV) file comprising a list of grid coordinates'
    w_use_csv.setToolTip(helpText_csv)
    grid.addWidget(w_use_csv, irow, 2)
    form.w_use_csv = w_use_csv    

    w_random = QRadioButton('Random cells')
    helpText = 'generate random coordinates'
    w_random.setToolTip(helpText)
    grid.addWidget(w_random, irow, 3)
    form.w_random = w_random

    lbl01b = QLabel('N coordinates')
    lbl01b.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl01b, irow, 4)

    w_inpt_choice = QButtonGroup()
    w_inpt_choice.addButton(w_use_spatial, SPATIAL)
    w_inpt_choice.addButton(w_use_csv, CSV_FILE)
    w_inpt_choice.addButton(w_random, RNDM_CELLS)
    w_inpt_choice.buttonClicked.connect(form.keyPress)
    form.w_inpt_choice = w_inpt_choice

    w_ncoords = QLineEdit()
    w_ncoords.setFixedWidth(WDGT_SIZE_40)
    grid.addWidget(w_ncoords, irow, 5)
    form.w_ncoords = w_ncoords

    # ======
    irow += 1
    w_csv_file = QPushButton('CSV file of coords')
    w_csv_file.setToolTip(helpText_csv)
    w_csv_file.clicked.connect(form.fetchCsvCoordsFile)
    grid.addWidget(w_csv_file, irow, 0)

    w_lbl20 = QLabel('')
    grid.addWidget(w_lbl20, irow, 1, 1, 4)
    form.w_lbl20 = w_lbl20

    w_lbl21 = QLabel('')
    grid.addWidget(w_lbl21, irow, 6)
    form.w_lbl21 = w_lbl21

    return irow

def commonSection(form, grid, irow):

    # =================
    # hist_syears, hist_eyears, fut_syears, fut_eyears, scenarios = get_wthr_parms(form, 'CRU')

    form.depths = list([30,100]) # soil depths

    luTypes = {}; lu_type_abbrevs = {}
    for lu_type, abbrev, ilu in zip(LU_DEFNS['lu_type'], LU_DEFNS['abbrev'], LU_DEFNS['ilu']):
        luTypes[lu_type] = ilu
        lu_type_abbrevs[lu_type] = abbrev

    form.land_use_types = luTypes
    form.lu_type_abbrevs = lu_type_abbrevs

    # equilibrium mode
    # ================
    irow += 1
    lbl12 = QLabel('Equilibrium mode:')
    lbl12.setAlignment(Qt.AlignRight)
    helpText = 'mode of equilibrium run, generally OK with 9.5'
    lbl12.setToolTip(helpText)
    grid.addWidget(lbl12, irow, 0)

    w_equimode = QLineEdit()
    w_equimode.setText(EQUIMODE_DFLT)
    w_equimode.setFixedWidth(WDGT_SIZE_60)
    grid.addWidget(w_equimode, irow, 1)
    form.w_equimode = w_equimode

    # soil switches
    # =============
    w_use_dom_soil = QCheckBox('Use most dominant soil')
    helpText = 'Each HWSD grid cell can have up to 10 soils. Select this option to use most dominant soil and\n' \
               ' discard all others. The the most dominant soil is defined as having the highest percentage coverage ' \
               ' of all the soils for that grid cell'
    w_use_dom_soil.setToolTip(helpText)
    grid.addWidget(w_use_dom_soil, irow, 2, 1, 2)
    form.w_use_dom_soil = w_use_dom_soil

    w_use_high_cover = QCheckBox('Use highest coverage soil')
    helpText = 'Each meta-cell has one or more HWSD mu global keys with each key associated with a coverage expressed \n' \
               ' as a proportion of the area of the meta cell. Select this option to use the mu global with the highest coverage,\n' \
               ' discard the others and aggregate their coverages to the selected mu global'
    w_use_high_cover.setToolTip(helpText)
    w_use_high_cover.setEnabled(False)
    grid.addWidget(w_use_high_cover, irow, 4, 1, 2)
    form.w_use_high_cover = w_use_high_cover

    irow += 1
    grid.addWidget(QLabel(''), irow, 2)  # spacer

    # line 9: resources
    # ===================
    irow += 1
    lbl10w = QLabel('Weather resource:')
    lbl10w.setAlignment(Qt.AlignRight)
    helpText = 'permissable weather dataset resources include CRU, Euro-CORDEX - see: http://www.euro-cordex.net, MERA and EObs'
    lbl10w.setToolTip(helpText)
    grid.addWidget(lbl10w, irow, 0)

    combo10w = QComboBox()
    for wthr_rsrc in form.wthr_rsrcs_generic:
        combo10w.addItem(wthr_rsrc)
    combo10w.setFixedWidth(WDGT_SIZE_100)
    form.combo10w = combo10w
    grid.addWidget(combo10w, irow, 1)

    # scenarios
    # =========
    lbl10 = QLabel('Scenario:')
    lbl10.setAlignment(Qt.AlignRight)
    helpText = 'Ecosse requires future average monthly precipitation and temperature derived from climate models.\n' \
        + 'The data used here is ClimGen v1.02 created on 16.10.08 developed by the Climatic Research Unit\n' \
        + ' and the Tyndall Centre. See: http://www.cru.uea.ac.uk/~timo/climgen/'

    lbl10.setToolTip(helpText)
    grid.addWidget(lbl10, irow, 2)

    # use filler scenarios, start and years - these are populated when the configuration file is read
    # ===============================================================================================
    combo10s = QComboBox()
    combo10s.setFixedWidth(WDGT_SIZE_100)
    grid.addWidget(combo10s, irow, 3)
    form.combo10s = combo10s

    # realisations
    # =============
    lbl10r = QLabel('Realisation:')
    lbl10r.setAlignment(Qt.AlignRight)
    helpText = ''
    lbl10r.setToolTip(helpText)
    grid.addWidget(lbl10r, irow, 4)

    # use filler scenarios, start and years - these are populated when the configuration file is read
    # ===============================================================================================
    combo10r = QComboBox()
    combo10r.setFixedWidth(WDGT_SIZE_40)
    grid.addWidget(combo10r, irow, 5)
    form.combo10r = combo10r

    # Historic
    # ========
    irow += 1
    lbl09s = QLabel('Historic start year:')
    lbl09s.setAlignment(Qt.AlignRight)
    helpText = 'Ecosse requires long term average monthly precipitation and temperature\n' \
            + 'which is derived from datasets managed by Climatic Research Unit (CRU).\n' \
            + ' See: http://www.cru.uea.ac.uk/about-cru'
    lbl09s.setToolTip(helpText)
    grid.addWidget(lbl09s, irow, 0)

    combo09s = QComboBox()
    combo09s.setFixedWidth(WDGT_SIZE_60)
    grid.addWidget(combo09s, irow, 1)
    form.combo09s = combo09s

    lbl09e = QLabel('End year:')
    lbl09e.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl09e, irow, 2)

    combo09e = QComboBox()
    combo09e.setFixedWidth(WDGT_SIZE_60)
    grid.addWidget(combo09e, irow, 3)
    form.combo09e = combo09e

    # Simulation years    
    # ================
    irow += 1
    lbl11s = QLabel('Simulation start year:')
    helpText = 'Simulation start and end years determine the number of growing seasons to simulate\n' \
            + 'CRU and CORDEX resources run to 2100 whereas EObs resource runs to 2017'
    lbl11s.setToolTip(helpText)
    lbl11s.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl11s, irow, 0)

    combo11s = QComboBox()
    combo11s.setFixedWidth(WDGT_SIZE_60)
    grid.addWidget(combo11s, irow, 1)
    form.combo11s = combo11s

    lbl11e = QLabel('End year:')
    lbl11e.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl11e, irow, 2)

    combo11e = QComboBox()
    combo11e.setFixedWidth(WDGT_SIZE_60)
    grid.addWidget(combo11e, irow, 3)
    form.combo11e = combo11e
    
    w_ave_wthr = QCheckBox('Use average weather')
    helpText = 'Select this option to use average weather, from the CRU year range, for\n' \
               ' the climate file for each of the simulation years'
    w_ave_wthr.setToolTip(helpText)
    grid.addWidget(w_ave_wthr, irow, 4, 1, 2)
    form.w_ave_wthr = w_ave_wthr

    irow += 1
    grid.addWidget(QLabel(''), irow, 2)     # spacer

    # row 13
    # ======
    irow += 1
    w_lu_pi_file = QPushButton('Land-use PI file')
    helpText = 'Option to select a JSON file comprising year index, land-use and plant input (tonnes per hectare)'
    w_lu_pi_file.setToolTip(helpText)
    w_lu_pi_file.clicked.connect(form.fetchLuPiJsonFile)
    grid.addWidget(w_lu_pi_file, irow, 1)

    w_lbl13 = QLabel('')
    grid.addWidget(w_lbl13, irow, 2, 1, 4)
    form.w_lbl13 = w_lbl13

    # for message from check_lu_pi_json_fname
    # =======================================
    irow += 1
    w_lbl14 = QLabel('')
    grid.addWidget(w_lbl14, irow, 2, 1, 5)
    form.w_lbl14 = w_lbl14

    # MK addition for PI NC
    # =====================
    irow += 1
    w_use_pi_nc = QCheckBox('Use pi NC file')
    w_use_pi_nc.setToolTip(helpText)
    grid.addWidget(w_use_pi_nc, irow, 0)
    form.w_use_pi_nc = w_use_pi_nc

    w_pi_nc = QPushButton('Plant input NC')
    helpText = 'Select NetCDF file of plant inputs'
    w_pi_nc.setToolTip(helpText)
    w_pi_nc.setEnabled(True)
    grid.addWidget(w_pi_nc, irow, 1)
    w_pi_nc.clicked.connect(form.fetchPiNcFile)

    lbl_pi_nc = QLabel()
    grid.addWidget(lbl_pi_nc, irow, 2, 1, 4)
    form.w_lbl_pi_nc = lbl_pi_nc

    # =========
    irow += 1
    lbl15 = QLabel('Select PI NC variable:')
    lbl15.setAlignment(Qt.AlignRight)
    helpText = 'Select yield variable'
    lbl15.setToolTip(helpText)
    grid.addWidget(lbl15, irow, 0)

    w_combo15 = QComboBox()
    w_combo15.setFixedWidth(120)
    form.w_combo15 = w_combo15
    grid.addWidget(w_combo15, irow, 1, 1, 2)

    return irow

def save_clicked(form):
    """
    write last GUI selections
    """
    write_config_file(form)
    write_study_definition_file(form)

    return

def exit_clicked(form, write_config_flag = True):
    """
    write last GUI selections
    """
    if write_config_flag:
        save_clicked(form)

    # close various files
    if hasattr(form, 'fobjs'):
        for key in form.fobjs:
            form.fobjs[key].close()

    # close logging
    try:
        form.lgr.handlers[0].close()
    except AttributeError:
        pass

    form.close()

def change_config_file(form):
    """
    identify and read the new configuration file
    """
    new_study = form.combo00s.currentText()
    new_config = 'global_ecosse_config_hwsd_' + new_study
    config_file = normpath(form.sttngs['config_dir'] + '/' + new_config + '.json')

    if isfile(config_file):
        form.config_file = config_file
        read_config_file(form)
        form.study = new_study
        form.w_study.setText(new_study)
    else:
        print('Could not locate ' + config_file)

    return

def study_text_changed(form):
    """
     replace spaces with underscores and rebuild study list
     """
    study = form.w_study.text()
    form.w_study.setText(study.replace(' ','_'))
