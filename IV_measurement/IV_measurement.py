import sys
import os
import time
import numpy as np
import pyqtgraph as pg

from PyQt4 import uic, QtGui, QtCore

from keithley24xx import Keithley24XX




pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', None) #'w')
pg.setConfigOption('foreground','k')


class IV_Experiment:

    def __init__(self):
        self.gate_keithley = None
        self.drain_keithley = None
        
        self.measurement_type = None
        self.gate_range = None
        self.drain_range = None
        self.hardware_sweep = True
        self.integration_time = None
        self.current_compliance = None
        self.set_measure_delay = None

        self.experiment_name = None
        self.measurement_name = None
        self.measurement_count = None
        self.working_folder = None

    def init_hardware(self, drain_keithley_resource, gate_keithley_resource):
        self.drain_keithley = Keithley24XX(drain_keithley_resource)
        self.gate_keithley = Keithley24XX(gate_keithley_resource)

    def open_experiment(self, working_folder, measurement_name, measurement_count):
        self.working_folder = working_folder
        self.measurement_name = measurement_name
        self.measurement_count = measurement_count

    def prepare_experiment(self, measurement_type, gate_range, drain_range, hardware_sweep, integration_time, current_compliance, set_measure_delay):
        self.measurement_type = measurement_type
        self.gate_range = gate_range
        self.drain_range = drain_range
        self.hardware_sweep = hardware_sweep
        self.integration_time = integration_time
        self.current_compliance = current_compliance
        self.set_measure_delay = set_measure_delay


    def prepare_hardware(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    


mainViewBase, mainViewForm = uic.loadUiType("UI_IV_Measurement.ui")
class MainView(mainViewBase, mainViewForm):
    def __init__(self, parent = None):
        super(mainViewBase, self).__init__(parent)
        self.setupUi(self)

    @QtCore.pyqtSlot()
    def on_folderBrowseButton_clicked(self):
        print("Select folder")
        
        folder_name = os.path.abspath(QtGui.QFileDialog.getExistingDirectory(self,caption="Select Folder"))#, directory = self._settings.working_directory))
        
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setText("This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setDetailedText(folder_name)
        msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        retval = msg.exec_()
        return retval

    @QtCore.pyqtSlot()
    def on_startButton_clicked(self):
        print("start")
        

    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        print("stop")
        


if __name__== "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("LegacyNoiseMeasurementSetup")
    #app.setStyle("cleanlooks")

    #css = "QLineEdit#sample_voltage_start {background-color: yellow}"
    #app.setStyleSheet(css)
    #sample_voltage_start

    wnd = MainView()
    wnd.show()

    sys.exit(app.exec_())