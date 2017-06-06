import sys
import time

from PyQt4 import uic, QtGui, QtCore
from nodes import ExperimentSettings, Node, SettingsModel
from configuration import Configuration








  














class Experiment:
    def __init__(self):
        self.__hardware_settings = None
        self.__exp_settings = ExperimentSettings()
        self.__initialize_hardware()

        self._measured_temp_start = 0;
        self._measured_temp_end = 0;

        self._measured_main_voltage_start = 0;
        self._measured_main_voltage_end = 0;

        self._measured_sample_voltage_start = 0;
        self._measured_samole_voltage_end = 0;
        
        self._measured_gate_voltage_start = 0;
        self._measured_gate_voltage_end = 0;

        self._sample_current_start = 0;
        self._sample_current_end = 0;

        self._sample_resistance_start = 0;
        self._sample_resistance_end = 0;

        self._equivalent_resistance_start = 0;
        self._equivalent_resistance_end = 0;

    def __initialize_settings(self, settings):
        assert isinstance(settings, ExperimentSettings)
        self.__exp_settings = settings


    def __initialize_hardware(self):
        #self.__dynamic_signal_analyzer = HP3567A(self.__hardware_settings["analyzer"])
        #self.__arduino_controller = ArduinoController(self.__hardware_settings["arduino_controller"])
        #self.__drain_multimeter = HP34401A(self.__hardware_settings["drain_multimeter"])
        #self.__main_gate_multimeter = HP34401A(self.__hardware_settings["main_gate_multimeter"])
        pass


    def output_curve_measurement_function(self):
        if self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            for vfg in self.__exp_settings.vfg_range:
                for vds in self.__exp_settings.vds_range:
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in self.__exp_settings.vds_range:
                    self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
             for vfg in self.__exp_settings.vfg_range:
                    self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        #foreach vfg_voltage in Vfg_range 
        #    foreach vds_voltage in Vds_range
        #       single_value_measurement(vds_voltage,vfg_voltage)
        

    def transfer_curve_measurement_function(self):
        if self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            for vds in self.__exp_settings.vds_range:
                for vfg in self.__exp_settings.vfg_range:
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in self.__exp_settings.vds_range:
                    self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
             for vfg in self.__exp_settings.vfg_range:
                    self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        # foreach vds_voltage in Vds_range
        #     foreach vfg_voltage in Vfg_range 
        #       single_value_measurement(vds_voltage,vfg_voltage)
    
    def set_front_gate_voltage(self,voltage):
        pass

    def set_drain_source_voltage(self,voltage):
        pass

    def set_voltage(self, voltage):
        pass   

    def single_value_measurement(self, drain_source_voltage, gate_voltage):
        self.set_drain_source_voltage(drain_source_voltage)
        self.set_front_gate_voltage(gate_voltage)
        self.set_drain_source_voltage(drain_source_voltage) ## specifics of the circuit!!! to correct the value of dropped voltage on opened channel
        self.perform_single_measurement()
        #set vds_voltage
        # set vfg voltage
        # stabilize voltage
        # perform_single_measurement()
        

    def non_gated_structure_meaurement_function(self):
        if self.__exp_settings.use_set_vds_range:
             for vds in self.__exp_settings.vds_range:
                    self.non_gated_single_value_measurement(vds)
        else:
            self.non_gated_single_value_measurement(self.__exp_settings.drain_source_voltage)

        # foreach vds_voltage in Vds_range
        #  non_gated_single_value_measurement(vds)

    def non_gated_single_value_measurement(self, drain_source_voltage):
        self.set_drain_source_voltage(drain_source_voltage)
        self.perform_non_gated_single_measurement()
        #set vds_voltage
        # stabilize voltage
        # perform_single_measurement()
        pass

   

    def generate_experiment_function(self):
        func = None
        if not self.__exp_settings.meas_gated_structure:# non gated structure measurement
            func = self.non_gated_structure_meaurement_function
        elif self.__meas_characteristic_type == 0: #output curve
            func = self.output_curve_measurement_function
        elif self.__meas_characteristic_type == 1: #transfer curve
            func = self.transfer_curve_measurement_function
        else: 
            raise AssertionError("function was not selected properly")

        if self.__exp_settings.use_transistor_selector:
            def execution_function(self):
                for transistor in self.__exp_settings.transistor_list:
                    func()
            return execution_function

        return func






    def perform_non_gated_single_measurement(self):
        #set overload_rejection
        #self.__dynamic_signal_analyzer.switch_overload_rejection(self.__exp_settings.overload_rejecion)
        #calibrate
        #if self.__exp_settings.calibrate_before_measurement:
        #    self.__dynamic_signal_analyzer.calibrate()
        
        #set averaging
        #self.__dynamic_signal_analyzer.set_average_count(self.__exp_settings.averages)

        #set display updates
        #self.__dynamic_signal_analyzer.set_display_update_rate(self.__exp_settings.display_refresh)

        #measure_temperature
        #if self.__exp_settings.need_measure_temperature:
        #    raise NotImplementedError()

        #switch Vfg to Vmain


        #measure Vmain
        #calculate Isample ,Rsample
        #measure spectra 
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #calculate resulting spectra
        #write data to measurement file and experiment file
        print("performing perform_non_gated_single_measurement")
        #pass
        

    def perform_single_measurement(self):
        #calibrate
        #set overload_rejection
        #set averaging
        #measure_temperature
        #measure Vds, Vfg
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #measure spectra 
        #measure Vds, Vfg
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #calculate resulting spectra
        #write data to measurement file and experiment file
        print("performing perform_single_measurement")
        #pass


    def perform_experiment(self):
        function_to_execute = self.generate_experiment_function()
        function_to_execute()







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

    def show_range_selector(self,model):
        dialog = RangeSelectorView(model)
        result = dialog.exec_()
        print(result)

    @QtCore.pyqtSlot()
    def on_VdsRange_clicked(self):
        print("Vds range")
        self.show_range_selector(None)

    @QtCore.pyqtSlot()
    def on_VfgRange_clicked(self):
        print("Vfg range")
        self.show_range_selector(None)

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

    #def set


def update():
    print("update") 

if __name__== "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("LegacyNoiseMeasurementSetup")
    app.setStyle("cleanlooks")

    wnd = MainView()
    wnd.show()

    sys.exit(app.exec_())



    #ard = ArduinoController("COM4", 115200)
    ##ard.open();
    ##var = ard.read_idn()
    ##print(var)
    #time.sleep(2)
    #for i in range(1,33,1):
    #    ard.switch_channel(i,True)
    #    time.sleep(0.3)
    #    ard.switch_channel(i,False)
    #var = ard.read_idn()
    #print(var)

    #ard.set_motor_speed(1,200)
    #ard.set_motor_speed(1 ,0)


    #ard.close()
    #    time.sleep(1)
    #    print(i)
    #    ard.write("2,{0},1;".format(i).encode())


    #m1 = HP34401A("GPIB0::23::INSTR")
    #m1.clear_status()
    #m1.reset()
    
    #m1.switch_beeper(False)
    #m1.set_nplc(0.1)
    #m1.set_trigger_count(10)
    #m1.switch_high_ohmic_mode(False)
    #m1.set_function(HP34401A_FUNCTIONS.AVER)
    
    #m1.switch_stat(True)
    #m1.switch_autorange(True)
    #m1.init_instrument()
    #print(m1.read_average())
    #m1.switch_stat(False)
    #print(m1.read_voltage())
    

    #res = "GPIB0::6::INSTR"
    #dev = HP3567A(res)
    #dev.abort()
    #dev.calibrate()
    #dev.set_source_voltage(6.6)
    #dev.output_state(True)
    #time.sleep(2)
    #dev.output_state(False)
    #print(HP35670A_MODES.FFT)
    #dev.select_instrument_mode(HP35670A_MODES.FFT)
    #dev.switch_input(HP35670A_INPUTS.INP2, False)
    #dev.select_active_traces(HP35670A_CALC.CALC1, HP35670A_TRACES.A)
    ##dev.select_real_format(64)
    #dev.select_ascii_format()
    #dev.select_power_spectrum_function(HP35670A_CALC.CALC1)
    #dev.select_voltage_unit(HP35670A_CALC.CALC1)
    #dev.switch_calibration(False)
    #dev.set_average_count(10)
    #dev.set_display_update_rate(2)
    #dev.set_frequency_resolution(1600)
    #dev.set_frequency_start(64.0)
    #dev.set_frequency_stop(102.4e3)

    #print(dev.get_points_number(HP35670A_CALC.CALC1))


    #dev.init_instrument()
    #dev.wait_operation_complete()

    #print(dev.get_data(HP35670A_CALC.CALC1))
