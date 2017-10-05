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


mainViewBase, mainViewForm = uic.loadUiType("UI_IV_Measurement.ui")
class MainView(mainViewBase, mainViewForm):
    def __init__(self, parent = None):
        super(mainViewBase, self).__init__(parent)
        self.setupUi(self)


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