#-------------------------------------------------------------------------------
# Name:
# Purpose:     Creates a GUI with five adminstrative levels plus country
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'GlblEcsseHwsdGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from os.path import join, normpath
from os import walk, getcwd, system, remove
from time import time
from shutil import rmtree

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit,
                                            QComboBox, QPushButton, QCheckBox, QFileDialog, QTextEdit, QMessageBox)

from shape_funcs import format_bbox, calculate_area
from common_componentsGUI import (commonSection, change_config_file, study_text_changed,
                                                                            exit_clicked, save_clicked, input_choices)
from glbl_ecss_cmmn_cmpntsGUI import calculate_grid_cell
from glbl_ecss_cmmn_funcs import check_lu_pi_json_fname, write_study_definition_file
from mngmnt_fns_and_class import check_csv_coords_fname

from grid_cell_classes_fns import generate_osgb_sites
from grid_cell_high_level_fns import generate_grid_cell_sims

from weather_datasets import change_wthr_rsrc
from initialise_funcs import initiation, read_config_file, build_and_display_studies, write_runsites_config_file

from plant_input_fns import check_plant_input_nc
from set_up_logging import OutLog

WDGT_SIZE_100 = 100
WDGT_SIZE_80 = 80
WDGT_SIZE_150 = 150
WDGT_SIZE_40 = 40
PADDING = '   '

# run modes
# =========
SPATIAL = 1
CSV_FILE = 2
RNDM_CELLS = 3
RUN_MODES = [SPATIAL, CSV_FILE, RNDM_CELLS]
RUN_MODE_LABELS = {CSV_FILE: 'from CSV file', RNDM_CELLS: 'randomly'}

RESOLUTIONS = [1, 2, 4, 5, 10]

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

# ========================

class Form(QWidget):

    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        self.version = 'HWSD_grid'
        initiation(self)
        font = QFont(self.font())
        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)	# set spacing between widgets

        # line 0
        # ======
        irow = 0
        lbl00 = QLabel('Study:')
        lbl00.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl00, irow, 0)

        w_study = QLineEdit()
        w_study.setFixedWidth(WDGT_SIZE_150)
        grid.addWidget(w_study, irow, 1, 1, 2)
        self.w_study = w_study

        lbl00s = QLabel(PADDING + 'Studies:')
        lbl00s.setAlignment(Qt.AlignRight)
        helpText = 'list of studies'
        lbl00s.setToolTip(helpText)
        grid.addWidget(lbl00s, irow, 2)

        combo00s = QComboBox()
        for study in self.studies:
            combo00s.addItem(study)
        combo00s.setFixedWidth(WDGT_SIZE_150)
        grid.addWidget(combo00s, irow, 3, 1, 2)
        combo00s.currentIndexChanged[str].connect(self.changeConfigFile)
        self.combo00s = combo00s

        # UR lon/lat
        # ==========
        irow += 1
        lbl02a = QLabel('Upper right longitude:')
        lbl02a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl02a, irow, 0)

        w_ur_lon = QLineEdit()
        w_ur_lon.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ur_lon, irow, 1)
        self.w_ur_lon = w_ur_lon

        lbl02b = QLabel('latitude:')
        lbl02b.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl02b, irow, 2)

        w_ur_lat = QLineEdit()
        w_ur_lat.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ur_lat, irow, 3)
        self.w_ur_lat = w_ur_lat

        # LL lon/lat
        # ==========
        irow += 1
        lbl01a = QLabel('Lower left longitude:')
        lbl01a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl01a, irow, 0)

        w_ll_lon = QLineEdit()
        w_ll_lon.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ll_lon, irow, 1)
        self.w_ll_lon = w_ll_lon

        lbl01b = QLabel('latitude:')
        lbl01b.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl01b, irow, 2)

        w_ll_lat = QLineEdit()
        w_ll_lat.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ll_lat, irow, 3)
        w_ll_lat.setFixedWidth(80)
        self.w_ll_lat = w_ll_lat

        # report on bbox
        # ==============
        irow += 1
        lbl03a = QLabel('Study bounding box:')
        lbl03a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl03a, irow, 0)

        self.w_bbox = QLabel()
        grid.addWidget(self.w_bbox, irow, 1, 1, 5)

        # =================================
        irow = commonSection(self, grid, irow)  # create weather
        irow = input_choices(self, grid, irow)

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # ==============
        irow += 1
        lbl10 = QLabel('Operation progress:')
        lbl10.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl10, irow, 0)

        self.w_prgrss = QLabel()
        grid.addWidget(self.w_prgrss, irow, 1, 1, 5)

        # command line
        # ============
        irow += 1
        w_create_files = QPushButton("Create sim files")
        helpText = 'Generate ECOSSE simulation file sets corresponding to ordered HWSD global mapping unit set in CSV file'
        w_create_files.setToolTip(helpText)
        w_create_files.setEnabled(False)
        w_create_files.setFixedWidth(WDGT_SIZE_100)
        grid.addWidget(w_create_files, irow, 0)
        w_create_files.clicked.connect(self.createSimsClicked)
        self.w_create_files = w_create_files

        w_auto_spec = QCheckBox('Auto run Ecosse')
        helpText = 'Select this option to automatically run Ecosse'
        w_auto_spec.setToolTip(helpText)
        grid.addWidget(w_auto_spec, irow, 1)
        self.w_auto_spec = w_auto_spec

        w_run_ecosse = QPushButton('Run Ecosse')
        helpText = 'Select this option to create a configuration file for the spec.py script and run it.\n' \
                   + 'The spec.py script runs the ECOSSE programme'
        w_run_ecosse.setToolTip(helpText)
        w_run_ecosse.setFixedWidth(WDGT_SIZE_80)
        w_run_ecosse.clicked.connect(self.runEcosseClicked)
        grid.addWidget(w_run_ecosse, irow, 2)
        self.w_run_ecosse = w_run_ecosse

        w_clr_psh = QPushButton('Clear', self)
        helpText = 'Clear reporting window'
        w_clr_psh.setToolTip(helpText)
        w_clr_psh.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_clr_psh, irow, 3, alignment=Qt.AlignRight)
        w_clr_psh.clicked.connect(self.clearReporting)

        w_cancel = QPushButton("Cancel")
        helpText = 'Leaves GUI without saving configuration and study definition files'
        w_cancel.setToolTip(helpText)
        w_cancel.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_cancel, irow, 4)
        w_cancel.clicked.connect(self.cancelClicked)

        w_save = QPushButton("Save")
        helpText = 'Save configuration and study definition files'
        w_save.setToolTip(helpText)
        w_save.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_save, irow, 5)
        w_save.clicked.connect(self.saveClicked)

        w_exit = QPushButton("Exit", self)
        grid.addWidget(w_exit, irow, 6)
        w_exit.setFixedWidth(WDGT_SIZE_80)
        w_exit.clicked.connect(self.exitClicked)

        # ========
        irow += 1
        w_del_sims = QPushButton('Del sims', self)
        helpText = 'Delete all simulations'
        w_del_sims.setToolTip(helpText)
        w_del_sims.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_del_sims, irow, 3, alignment=Qt.AlignRight)
        w_del_sims.clicked.connect(self.delSims)

        # LH vertical box consists of png image
        # =====================================
        lh_vbox = QVBoxLayout()

        lbl20 = QLabel()
        lbl20.setPixmap(QPixmap(self.fname_png))
        lbl20.setScaledContents(True)

        lh_vbox.addWidget(lbl20)

        # add grid consisting of combo boxes, labels and buttons to RH vertical box
        # =========================================================================
        rh_vbox = QVBoxLayout()
        rh_vbox.addLayout(grid)

        # add reporting
        # =============
        bot_hbox = QHBoxLayout()
        w_report = QTextEdit()
        w_report.verticalScrollBar().minimum()
        w_report.setMinimumHeight(200)
        w_report.setMinimumWidth(1000)
        w_report.setStyleSheet('font: bold 10.5pt Courier')  # big jump to 11pt
        bot_hbox.addWidget(w_report, 1)
        self.w_report = w_report

        sys.stdout = OutLog(self.w_report, sys.stdout)
        # sys.stderr = OutLog(self.w_report, sys.stderr, QColor(255, 0, 0))

        # add LH and RH vertical boxes to main horizontal box
        # ===================================================
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(10)
        main_hbox.addLayout(lh_vbox)
        main_hbox.addLayout(rh_vbox, stretch = 1)

        # feed horizontal boxes into the window
        # =====================================
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_hbox)
        outer_layout.addLayout(bot_hbox)
        self.setLayout(outer_layout)

        # posx, posy, width, height
        self.setGeometry(200, 100, 690, 250)
        self.setWindowTitle('Global Ecosse Ver 2b - generate sets of ECOSSE input files based on HWSD grid')

        # reads and set values from last run
        # ==================================
        read_config_file(self)

        self.combo10w.currentIndexChanged[str].connect(self.wthrResourceChanged)
        self.w_ll_lat.textChanged[str].connect(self.bboxTextChanged)
        self.w_ll_lon.textChanged[str].connect(self.bboxTextChanged)
        self.w_ur_lat.textChanged[str].connect(self.bboxTextChanged)
        self.w_ur_lon.textChanged[str].connect(self.bboxTextChanged)

    def delSims(self):
        """

        """
        study = self.w_study.text()
        study_dir = join(self.sttngs['sims_dir'], study)
        num_sims = 0
        for directory, subdirs_raw, manifests in walk(study_dir):
            num_sims = len(subdirs_raw)
            nmanis = len(manifests)
            break

        if num_sims == 0 and nmanis == 0:
            print(WARN_STR + 'no grid_cells or manifests files to delete from study: ' + study)
            return

        mess_content = 'Will delete {} cells and {} manifest files from study: {}'.format(num_sims, nmanis, study)
        mess_content += '\n\n\t are you sure?'
        w_mess_box = QMessageBox()
        w_mess_box.setText(mess_content)
        w_mess_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        w_mess_box = w_mess_box.exec()

        if w_mess_box == QMessageBox.Yes:
            if num_sims > 0:
                for subdir in subdirs_raw:
                    grid_dir = join(study_dir, subdir)
                    rmtree(grid_dir, ignore_errors=True)

            if nmanis > 0:
                for mani in manifests:
                    mani_fn = join(study_dir, mani)
                    remove(mani_fn)

            print('Deleted {} cells and {} manifest files'.format(num_sims, nmanis))

        return

    def createSimsClicked(self):
        """

        """
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
            return

        # check for spaces
        # ================
        if study.find(' ') >= 0:
            print('*** study name must not have spaces ***')
            return

        self.study = study

        run_id = self.w_inpt_choice.checkedId()
        if run_id not in RUN_MODES:
            print(ERROR_STR + 'run mode {} not recognised'.format(run_id))
            return

        if run_id == SPATIAL:
            pass  # relic
        else:
            # CSV_FILE or RNDM_CELLS
            # ======================
            wthr_rsrc = self.combo10w.currentText()
            if wthr_rsrc != 'CHESS':
                print('Weather resource must be CHESS')
                return

            grid_cells = generate_osgb_sites(self, run_id)
            if grid_cells is None:
                return

            generate_grid_cell_sims(self, grid_cells)
            write_study_definition_file(self)

        # run further steps
        # =================
        if self.w_auto_spec.isChecked():
            self.runEcosseClicked()

        return

    def keyPress(self, bttnWdgtId):
        """

        """
        pass
        # print("Key was pressed, id is: ", self.w_inpt_choice.id(bttnWdgtId))

    def fetchCsvCoordsFile(self):
        """
        QFileDialog returns a tuple for Python 3.5, 3.6
        """
        fname = self.w_lbl20.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'CSV files (*.csv)')
        if fname != '':
            self.w_lbl20.setText(fname)
            print(check_csv_coords_fname(fname, self.w_lbl21))

    def clearReporting(self):
        """

        """
        self.w_report.clear()

    def wthrResourceChanged(self):
        """

        """
        change_wthr_rsrc(self)

    def fetchLuPiJsonFile(self):
        """
        QFileDialog returns a tuple for Python 3.5, 3.6
        """
        fname = self.w_lbl13.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'JSON files (*.json)')
        if fname != '':
            self.w_lbl13.setText(fname)
            self.w_lbl14.setText(check_lu_pi_json_fname(self))

    def resolutionChanged(self):

        granularity = 120
        calculate_grid_cell(self, granularity)

    def studyTextChanged(self):

        study_text_changed(self)

    def bboxTextChanged(self):
        """

        """
        try:
            bbox = list([float(self.w_ll_lon.text()), float(self.w_ll_lat.text()),
                float(self.w_ur_lon.text()), float(self.w_ur_lat.text())])
            area = calculate_area(bbox)
            self.w_bbox.setText(format_bbox(bbox, area))
            self.sttngs['bbox'] = bbox
        except ValueError as err:
            pass

    def runEcosseClicked(self):
        """
        components of the command string have been checked at startup
        """
        if write_runsites_config_file(self):

            # run the make simulations script
            # ===============================
            print('Working dir: ' + getcwd())
            start_time = time()
            cmd_str = self.python_exe + ' ' + self.runsites_py + ' ' + self.runsites_config_file
            system(cmd_str)
            end_time = time()
            print('Time taken: {}'.format(round(end_time - start_time)))

    def saveClicked(self):
        """

        """
        # check for spaces
        # ================
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
        else:
            if study.find(' ') >= 0:
                print('*** study name must not have spaces ***')
            else:
                save_clicked(self)
                build_and_display_studies(self, self.sttngs['glbl_ecsse_str'])

        return

    def cancelClicked(self):
        """

        """
        exit_clicked(self, write_config_flag = False)

    def exitClicked(self):
        """
        exit cleanly
        """
        # check for spaces
        # ================
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
        else:
            if study.find(' ') >= 0:
                print('*** study name must not have spaces ***')
            else:
                exit_clicked(self)

    def changeConfigFile(self):
        """
        permits change of configuration file
        """
        change_config_file(self)

    def fetchPiNcFile(self):
        """
        Select NetCDF file of plant inputs
        if user canels then fname is returned as an empty string
        """
        fname = self.w_lbl_pi_nc.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Select NetCDF of plant inputs', fname, 'NetCDF file (*.nc)')
        if fname != '':
            fname = normpath(fname)
            check_plant_input_nc(self, fname)
            self.w_lbl_pi_nc.setText(fname)

def main():
    """

    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
