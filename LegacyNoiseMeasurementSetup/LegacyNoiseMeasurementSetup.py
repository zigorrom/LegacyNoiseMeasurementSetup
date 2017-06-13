﻿import sys
import time
import numpy as np
from multiprocessing import JoinableQueue
from collections import deque


from PyQt4 import uic, QtGui, QtCore
from nodes import ExperimentSettings, Node, SettingsModel, ValueRange, HardwareSettings
from configuration import Configuration
from communication_layer import get_available_gpib_resources, get_available_com_resources
from plot import SpectrumPlotWidget
from experiment_handler import ProcessingThread, Experiment

class ExperimentController(QtCore.QObject):
    def __init__(self, spectrum_plot=None, timetrace_plot=None,parent = None):
        super().__init__(parent)
        if spectrum_plot:
            assert isinstance(spectrum_plot, SpectrumPlotWidget)
        self._spectrum_plot = spectrum_plot

        self._visualization_deque = deque(maxlen = 10)
        self._input_data_queue = JoinableQueue()

        self._processing_thread = ProcessingThread(self._input_data_queue, self._visualization_deque)
        self._experiment_thread = Experiment(self._input_data_queue)

        #assert isinstance(timetrace_plot, TimetracePlotWidget)
        #self._timetrace_plot = timetrace_plot

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._update_gui)
        self._counter = 0





    def _update_gui(self):
        try:
            print("refreshing: {0}".format(self._counter))
            self._counter+=1
            data = self._visualization_deque.popleft()
            dataX = data['f']
            dataY = data['d']
            #dataX = np.linspace(1,1600,1600,True)
            #dataY = 10**-9 * np.random.random(1600)
            self._spectrum_plot.update_spectrum(1,{'f':dataX, 'd': dataY})
            
        except Exception as e:
            raise e
            #print(str(e))


    def start(self):
        self._refresh_timer.start()
        self._experiment_thread.start()
        self._processing_thread.start()

    def stop(self):
        self._refresh_timer.stop()
        self._experiment_thread.stop()
        self._experiment_thread.join()
        
        self._input_data_queue.join()
        self._processing_thread.stop()
    

mainViewBase, mainViewForm = uic.loadUiType("UI_NoiseMeasurement.ui")
class MainView(mainViewBase,mainViewForm):
    def __init__(self, parent = None):
       super(mainViewBase,self).__init__(parent)
       self.setupUi(self)
       self._config  = Configuration()
       rootNode = self._config.get_node_from_path("Settings")#Node("settings")
       self.setSettings(rootNode)
       self.setupPlots()
       self._experiment_controller = ExperimentController(self._spectrumPlotWidget)
       

    def setupPlots(self):
        self._spectrumPlotWidget =  SpectrumPlotWidget(self.ui_plot,{0:(0,1600,1),1:(0,102400,64)})


    def setSettings(self, rootNode):
       
       settings = rootNode.getChildByName("ExperimentSettings")
       assert isinstance(settings,ExperimentSettings)
       self._settings = settings
       self._viewModel = SettingsModel(rootNode)
       
       self._dataMapper = QtGui.QDataWidgetMapper()
       self._dataMapper.setModel(self._viewModel)
       self._dataMapper.addMapping(self.ui_experimentName ,1)
       self._dataMapper.addMapping(self.ui_measurementName ,2)
       self._dataMapper.addMapping(self.ui_measurementCount ,3)
       self._dataMapper.addMapping(self.ui_calibrate ,4)
       self._dataMapper.addMapping(self.ui_overload_reject ,5)
       self._dataMapper.addMapping(self.ui_display_refresh ,6)
       self._dataMapper.addMapping(self.ui_averages ,7)
       self._dataMapper.addMapping(self.ui_use_homemade_amplifier ,8)
       #self._dataMapper.addMapping(self. ,9)
       #self._dataMapper.addMapping(self. ,10)
       self._dataMapper.addMapping(self.ui_second_amp_coeff ,11)
       self._dataMapper.addMapping(self.ui_load_resistance ,12)
       self._dataMapper.addMapping(self.ui_need_meas_temp ,13)
       self._dataMapper.addMapping(self.ui_meas_gated_structure ,14)
       self._dataMapper.addMapping(self.ui_meas_characteristic_type ,15,"currentIndex")
       self._dataMapper.addMapping(self.ui_use_dut_selector ,16)
       #self._dataMapper.addMapping(self. ,17)
       self._dataMapper.addMapping(self.ui_use_set_vds_range ,18)
       #self._dataMapper.addMapping(self. ,19)
       self._dataMapper.addMapping(self.ui_use_set_vfg_range ,20)
       #self._dataMapper.addMapping(self. ,21)
       self._dataMapper.addMapping(self.ui_front_gate_voltage ,22)
       self._dataMapper.addMapping(self.ui_drain_source_voltage ,23)
       
       QtCore.QObject.connect(self._viewModel, QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), self.on_data_changed)
       self._dataMapper.toFirst()

    def on_data_changed(self):
        print("view model changed")
        #s = XmlNodeSerializer()
        #xml = s.serialize(self._config.get_root_node())
        self._config.save_config()


    @QtCore.pyqtSlot()
    def on_ui_open_hardware_settings_clicked(self):
        print("open hardware settings")
        dialog = HardwareSettingsView()
        rootNode = self._config.get_root_node()
        viewModel = SettingsModel(rootNode)
        hardware_settings = self._config.get_node_from_path("HardwareSettings")
        assert isinstance(hardware_settings,HardwareSettings)
        idx = QtCore.QModelIndex()
        if hardware_settings!= rootNode:
            idx = viewModel.createIndex(hardware_settings.row(),0,hardware_settings)
        dialog.setModel(viewModel)
        dialog.setSelection(idx)
        result = dialog.exec_()
        print(result)

    @QtCore.pyqtSlot()
    def on_startButton_clicked(self):
        print("start")
        self._experiment_controller.start()

    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        print("stop")
        self._experiment_controller.stop()

    def show_range_selector(self,model, currentIndex):
        dialog = RangeSelectorView()
        dialog.setModel(model)
        dialog.setSelection(currentIndex)
        result = dialog.exec_()
        print(result)

    @QtCore.pyqtSlot()
    def on_VdsRange_clicked(self):
        print("Vds range")
        
        rootNode = self._config.get_root_node()
        rang = self._config.get_node_from_path("drain_source_range")
        viewModel = SettingsModel(rootNode)
        
        assert isinstance(rang,ValueRange)
        
        idx = QtCore.QModelIndex()
        if rang!= rootNode:
            idx = viewModel.createIndex(rang.row(),0,rang)

        self.show_range_selector(viewModel, idx)
       



    @QtCore.pyqtSlot()
    def on_VfgRange_clicked(self):
        print("Vfg range")

        rootNode = self._config.get_root_node()
        rang = self._config.get_node_from_path("front_gate_range")
        viewModel = SettingsModel(rootNode)
        
        assert isinstance(rang,ValueRange)
        
        idx = QtCore.QModelIndex()
        if rang!= rootNode:
            idx = viewModel.createIndex(rang.row(),0,rang)

        self.show_range_selector(viewModel, idx)


    @QtCore.pyqtSlot()
    def on_transistorSelector_clicked(self):
        dialog = DUTselectorView()
        result = dialog.exec_()
        print("Select transistors")

    @QtCore.pyqtSlot()
    def on_folderBrowseButton_clicked(self):
        print("Select folder")
        folder_name = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder")
        
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setText("This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setDetailedText(folder_name)
        msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        retval = msg.exec_()
        if retval and self._settings:
            self._settings.working_directory = folder_name
            
    
    @QtCore.pyqtSlot()
    def on_selectVoltageChangeOrder_clicked(self):
        print("selectVoltageChangeOrder")
        
    def closeEvent(self,event):
        self._config.save_config()

    

HardwareSettingsBase, HardwareSettingsForm = uic.loadUiType("UI_HardwareSettings.ui")
class HardwareSettingsView(HardwareSettingsBase, HardwareSettingsForm):
    def __init__(self,parent = None):
        super(HardwareSettingsBase,self).__init__(parent)
        self.setupUi(self)
        gpib_resources = get_available_gpib_resources()
        com_resources = get_available_com_resources()
        self.ui_analyzer.addItems(gpib_resources)
        self.ui_main_gate.addItems(gpib_resources)
        self.ui_sample.addItems(gpib_resources)
        self.ui_arduino.addItems(com_resources)
        self._dataMapper = QtGui.QDataWidgetMapper()

    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)

    def setModel(self, model):
        self._viewModel = model
        self._dataMapper.setModel(self._viewModel)
        self._dataMapper.addMapping(self.ui_analyzer ,2)
        self._dataMapper.addMapping(self.ui_main_gate ,3)
        self._dataMapper.addMapping(self.ui_sample ,4)
        #5 skipped in Hardware Settings node
        self._dataMapper.addMapping(self.ui_arduino ,6)
        self._dataMapper.addMapping(self.ui_sample_channel ,7,"currentIndex")
        self._dataMapper.addMapping(self.ui_gate_channel ,8,"currentIndex")





DUTselectorViewBase, DUTselectorViewForm = uic.loadUiType("UI_TransistorSelector.ui")
class DUTselectorView(DUTselectorViewBase,DUTselectorViewForm):
    def __init__(self,parent = None):
        super(DUTselectorViewBase,self).__init__(parent)
        self.setupUi(self)


rangeSelectorBase, rangeSelectorForm = uic.loadUiType("UI_RangeSelector.ui")
class RangeSelectorView(rangeSelectorBase,rangeSelectorForm):
    def __init__(self,parent = None):
        super(rangeSelectorBase,self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QtGui.QDataWidgetMapper()

    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)

    def setModel(self, model):
        self._viewModel = model
        self._dataMapper.setModel(self._viewModel)

        #rootNode = configuration.get_root_node()
        #self._viewModel = SettingsModel(rootNode)
        #self._range = configuration.get_node_from_path("drain_source_range")
        #assert isinstance(self._range,ValueRange)
        #parent = self._range.parent()
        #idx = QtCore.QModelIndex()
        #if parent != rootNode:
        #    idx = self._viewModel.createIndex(parent.row(),0,parent)
        #self._viewModel = SettingsModel(self._settings)

        #self._dataMapper.setModel(self._viewModel)
        self._dataMapper.addMapping(self.ui_start_val ,2)
        self._dataMapper.addMapping(self.ui_start_units ,3,"currentIndex")
        self._dataMapper.addMapping(self.ui_stop_val ,4)
        self._dataMapper.addMapping(self.ui_stop_units ,5,"currentIndex")
        self._dataMapper.addMapping(self.ui_count ,6)
        self._dataMapper.addMapping(self.ui_range_mode ,7,"currentIndex")
        
        #QtCore.QObject.connect(self._viewModel, QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), self.on_data_changed)
        #self._dataMapper.setRootIndex(idx)
        #self._dataMapper.toFirst()


    def on_data_changed(self):
        print("range changed")
        


def update():
    print("update") 

if __name__== "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("LegacyNoiseMeasurementSetup")
    app.setStyle("cleanlooks")

    wnd = MainView()
    wnd.show()

    sys.exit(app.exec_())



    


   

    