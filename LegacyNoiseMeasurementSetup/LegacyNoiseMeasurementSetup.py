﻿import sys
import time

from PyQt4 import uic, QtGui, QtCore
from nodes import ExperimentSettings, Node, SettingsModel, ValueRange
from configuration import Configuration


mainViewBase, mainViewForm = uic.loadUiType("UI_NoiseMeasurement.ui")
class MainView(mainViewBase,mainViewForm):
    def __init__(self, parent = None):
       super(mainViewBase,self).__init__(parent)
       self.setupUi(self)
       self._config  = Configuration()
       
       rootNode = self._config.get_node_from_path("Settings")#Node("settings")
       self.setSettings(rootNode)
       #self._settings = ExperimentSettings(parent = rootNode)
       
       #self._settings = ExperimentSettings()#parent = rootNode)
       #self.setModel(ExperimentSettingsViewModel(self._settings))
       #self._viewModel = ExperimentSettingsViewModel(self._settings)
       #self._dataMapper = QtGui.QDataWidgetMapper()

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
    def on_startButton_clicked(self):
        print("start")

    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        print("stop")

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

        self._dataMapper.setModel(self._viewModel)
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



    


   

    