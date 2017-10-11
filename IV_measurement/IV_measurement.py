import sys
import os
import time
import datetime
import numpy as np
import pyqtgraph as pg
import pandas as pd

from PyQt4 import uic, QtGui, QtCore
from PyQt4.QtCore import QThread

import configparser


from communication_layer import get_available_gpib_resources, get_available_com_resources
from keithley24xx import Keithley24XX
from range_handlers import float_range



pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', None) #'w')
pg.setConfigOption('foreground','k')

INTEGRATION_SPEEDS = ["Slow", "Middle", "Fast"]
INTEGRATION_SLOW,INTEGRATION_MIDDLE, INTEGRATION_FAST = INTEGRATION_SPEEDS

MEASUREMENT_TYPES = ["Output", "Transfer"]
OUTPUT_MEASUREMENT, TRANSFER_MEASUREMENT = MEASUREMENT_TYPES

class MeasurementThread(QThread):
    measurementStarted = QtCore.pyqtSignal()
    measurementStopped = QtCore.pyqtSignal()
    measurementProgressChanged =QtCore.pyqtSignal(int)

    def __init__(self, experiment):
        QThread.__init__(self)
        self.alive = True
        assert isinstance(experiment, IV_Experiment), "Not expectable experiment type"
        self.experiment = experiment

    def __del__(self):
        self.wait()

    def stop(self):
        self.alive = False

    def run(self):
        self.experiment.perform_measurement()
        

class IV_Experiment(QThread):
    measurementStarted = QtCore.pyqtSignal()
    measurementStopped = QtCore.pyqtSignal()
    measurementProgressChanged =QtCore.pyqtSignal(int)

    def __init__(self):
        QThread.__init__(self)
        self.alive = True

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

    def __del__(self):
        self.wait()

    def stop(self):
        self.alive = False
        self.wait()

    def run(self):
        self.perform_measurement()

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

    def __prepare_device(self,device):
        assert isinstance(device, Keithley24XX), "Wrong device type. Expected Keithley24XX"
        #abort operations
        device.Abort()
        #reset devices
        device.Reset()
        #switch off buffer control
        device.SelectTraceBufferControl(Keithley24XX.NEVER_TRACE_CONTROL)
        #clear buffer
        device.ClearBuffer()
        #switch concurrent measurement off
        device.SetConcurrentMeasurement(Keithley24XX.STATE_OFF)

        device.SetVoltageSourceFunction()
        
        device.SetCurrentSenseFunction()

        assert self.integration_time in INTEGRATION_SPEEDS, "Integration time is not set correct"

        nplc = 1
        if self.integration_time == INTEGRATION_SLOW:
            nplc = 1
        elif self.integration_time == INTEGRATION_MIDDLE:
            nplc = 0.1
        elif self.integration_time == INTEGRATION_FAST:
            nplc = 0.01
        device.SetVoltageNPLC(nplc)

        device.SetCurrentSenseCompliance(self.current_compliance)

        device.SetDelay(self.set_measure_delay)

    def __prepare_hardware_sweep(self, indep_device, dep_device, sweep_range):
        assert isinstance(sweep_range, float_range), "sweep range is not of type float_range"
        
        indep_device.SetSweepStartVoltage(sweep_range.start)
        indep_device.SetSweepStopVoltage(sweep_range.stop)
        indep_device.SetSweepPoints(sweep_range.length)
        confirm_points = indep_device.GetSweepPoints()
        assert sweep_range.length == confirm_points, "range setting error"
        indep_device.SetSweepVoltageSourceMode()
        indep_device.SetSweepRanging(Keithley24XX.RANGING_AUTO)
        indep_device.SetSweepSpacing(Keithley24XX.SPACING_LIN)

        indep_device.SetTriggerCount(confirm_points)
        indep_device.SetTraceBufferSize(confirm_points)

        dep_device.SetTriggerCount(confirm_points)
        dep_device.SetTraceBufferSize(confirm_points)

        #indep_device.SelectTraceBufferControl(Keithley24XX.NEXT_TRACE_CONTROL)
        #dep_device.SelectTraceBufferControl(Keithley24XX.NEXT_TRACE_CONTROL)
        
        self.__configure_device_trigger_link(indep_device, dep_device)

    def __prepare_software_sweep(self,device):
        device.SetFixedVoltageSourceMode()

    def __configure_device_trigger_link(self, independent_device, dependent_device):
        assert isinstance(independent_device, Keithley24XX), "Wrong type for independent device"
        assert isinstance(dependent_device, Keithley24XX), "Wrong type for dependent device"
        
        dependent_device.SetTriggerSource(Keithley24XX.TRIG_TLIN)
        dependent_device.SetTriggerInputEventDetection(Keithley24XX.TRIG_SOUR_EVENT)
        dependent_device.SetTriggerInputLine(1)
        dependent_device.SetTriggerOutputLine(2)
        dependent_device.SetTriggerOutputEvent(Keithley24XX.TRIG_SENS_EVENT)

        independent_device.SetTriggerSource(Keithley24XX.TRIG_TLIN)
        independent_device.SetTriggerInputEventDetection(Keithley24XX.TRIG_SENS_EVENT)
        independent_device.SetTriggerOutputEvent(Keithley24XX.TRIG_SOUR_EVENT)
        independent_device.SetTriggerOutputLine(1)
        independent_device.SetTriggerInputLine(2)

    def __prepare_output_measurement(self):
        if self.hardware_sweep:
            print("using hardware sweep")
            self.__prepare_hardware_sweep(self.drain_keithley, self.gate_keithley, self.drain_range)
            self.__prepare_software_sweep(self.gate_keithley)
            
        else:
            print("using software sweep")
            self.__prepare_software_sweep(self.gate_keithley)
            self.__prepare_software_sweep(self.drain_keithley)

    def __prepare_transfer_measurement(self):
        if self.hardware_sweep:
            print("using hardware sweep")
            self.__prepare_hardware_sweep(self.gate_keithley,self.drain_keithley, self.gate_range)
            self.__prepare_software_sweep(self.drain_keithley)
        else:
            print("using software sweep")
            self.__prepare_software_sweep(self.drain_keithley)
            self.__prepare_software_sweep(self.gate_keithley)

    def prepare_hardware(self):
        self.__prepare_device(self.drain_keithley)
        self.__prepare_device(self.gate_keithley)

        if self.measurement_type == OUTPUT_MEASUREMENT:
            self.__prepare_output_measurement()
        elif self.measurement_type == TRANSFER_MEASUREMENT:
            self.__prepare_transfer_measurement()
        else:
            raise Exception("Measurement type error")

    
    def __perform_hardware_sweep(self, independent_device, independent_range, dependent_device, dependent_range, independent_variable_name, dependent_variable_name):
        assert isinstance(independent_device, Keithley24XX), "Wrong type for independent device"
        assert isinstance(dependent_device, Keithley24XX), "Wrong type for dependent device"
        NUMBER_OF_ELEMENTS_READ_FROM_DEVICE = 5
        cols = "{0} voltage; {0} current; {0} timestamp; {1} voltage; {1} current; {1} timestamp".format(independent_variable_name.title(), dependent_variable_name.title()).split(';')
        filename_format = "{0}_{1}_{2}.dat"
        for dependent_voltage in np.linspace(dependent_range.start, dependent_range.stop, dependent_range.length, True):
            if not self.alive:
                print("Measurement abort")
                return

            independent_device.OutputOn()
            dependent_device.OutputOn() 
            dependent_device.SetVoltageAmplitude(dependent_voltage)
                
            dependent_device.SelectTraceBufferControl(Keithley24XX.NEXT_TRACE_CONTROL)
            independent_device.SelectTraceBufferControl(Keithley24XX.NEXT_TRACE_CONTROL)

            independent_device.Initiate()
            dependent_device.Initiate()
                
            independent_device.WaitOperationCompleted()
            dependent_device.WaitOperationCompleted()

            independent_device.OutputOff()
            dependent_device.OutputOff() 
            
            strData = independent_device.ReadTraceData() #k.FetchData()
            strData2 = dependent_device.ReadTraceData() #k2.FetchData()

            independent_device.ClearBuffer()
            dependent_device.ClearBuffer()
                
            indep_data = np.fromstring(strData, sep=',')
            dep_data = np.fromstring(strData2, sep=',')
            
            indep_data = indep_data.reshape((independent_range.length,NUMBER_OF_ELEMENTS_READ_FROM_DEVICE)).T
            dep_data = dep_data.reshape((independent_range.length,NUMBER_OF_ELEMENTS_READ_FROM_DEVICE)).T

            indep_voltages, indep_currents, indep_resistances, indep_times, indep_status  = indep_data
            dep_voltages, dep_currents, dep_resistances, dep_times, dep_status  = dep_data

            res_array = np.vstack((indep_voltages, indep_currents, indep_times, dep_voltages, dep_currents, dep_times)).T
            df = pd.DataFrame(res_array,index = np.arange(independent_range.length), columns = cols)
            filename = os.path.join(self.working_folder,filename_format.format(self.measurement_name,self.measurement_count, datetime.datetime.now().strftime("%Y-%m-%dH%HM%MS%S") )) 
            df.to_csv(filename, index = False)
            #indep_voltages, indep_currents, indep_resistances, indep_times, indep_status  = data
            #dep_voltages, dep_currents, dep_resistances, dep_times, dep_status  = data2
            #print("VG={0}".format(dependent_voltage))
            #print(dep_voltages)
            #print(indep_currents)


    def _perform_hardware_sweep_for_measurement_type(self):
        drain_var, gate_var = ("drain","gate")
        if self.measurement_type == OUTPUT_MEASUREMENT:
            self.__perform_hardware_sweep(self.drain_keithley, self.drain_range,self.gate_keithley,self.gate_range, drain_var, gate_var)
        elif self.measurement_type == TRANSFER_MEASUREMENT:
            self.__perform_hardware_sweep(self.gate_keithley,self.gate_range, self.drain_keithley, self.drain_range, gate_var, drain_var)



    def _perform_software_sweep(self):
        raise NotImplementedError("Software sweep is in the development")
        #if self.measurement_type == OUTPUT_MEASUREMENT:
        #    pass
        #elif self.measurement_type == TRANSFER_MEASUREMENT:
        #    pass

    def perform_measurement(self):
        if self.hardware_sweep:
            self._perform_hardware_sweep_for_measurement_type()
        else:
            self._perform_software_sweep()


    
    


mainViewBase, mainViewForm = uic.loadUiType("UI_IV_Measurement.ui")
class MainView(mainViewBase, mainViewForm):
    config_filename = 'configuration.ini'
    config_file_section_name = "UI_Options"
    (measurement_type_option,
                drain_keithley_resource_option, 
                gate_keithley_resource_option, 
                drain_start_option, 
                drain_stop_option, 
                drain_points_option, 
                gate_start_option, 
                gate_stop_option, 
                gate_points_option, 
                hardware_sweep_option, 
                integration_time_option, 
                current_compliance_option,
                set_measure_delay_option,
                experiment_name_option,
                measurement_name_option,
                measurement_count_option,
                working_directory_option) = ("type",
                                             "ds_resource",
                                             "gs_resource",
                                             "drain_start",
                                             "drain_stop",
                                             "drain_points",
                                             "gate_start",
                                             "gate_stop" ,
                                             "gate_points" ,
                                             "hardware_sweep",
                                             "integration_time",
                                             "current_compliance",
                                             "set_measure_delay",
                                             "experiment_name",
                                             "measuremtn_name",
                                             "measurement_count",
                                             "working_directory")

    def __init__(self, parent = None):
        super(mainViewBase, self).__init__(parent)
        self.setupUi()
        self.experiment = None
        self.working_directory = ""

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
        if retval:
            self.working_directory = folder_name
        return retval

    def setupUi(self):
        super(MainView, self).setupUi(self)
        
        self.ui_measurement_type.addItems(MEASUREMENT_TYPES)
        gpib_resources = get_available_gpib_resources()
        self.ui_ds_resource.addItems(gpib_resources)
        self.ui_gs_resource.addItems(gpib_resources)
        self.ui_integration_time.addItems(INTEGRATION_SPEEDS)

        config = configparser.ConfigParser()
        config.read(self.config_filename)




    def __get_values_from_ui(self):
        measurement_type = self.ui_measurement_type.currentText()

        drain_keithley_resource = self.ui_ds_resource.currentText()
        gate_keithley_resource = self.ui_gs_resource.currentText()

        drain_range = float_range(self.ui_ds_start.value(), self.ui_ds_stop.value(), len = self.ui_ds_points.value())
        gate_range =  float_range(self.ui_gs_start.value(), self.ui_gs_stop.value(), len = self.ui_gs_points.value())

        hardware_sweep = self.ui_hardware_sweep.isChecked()
        integration_time = self.ui_integration_time.currentText()
        current_compliance = self.ui_current_compliance.value()
        set_measure_delay = self.ui_set_meas_delay.value()

        experiment_name = self.ui_experimentName.text()
        measurement_name = self.ui_measurementName.text()
        measurement_count = self.ui_measurementCount.value()

        return (measurement_type,
                drain_keithley_resource, 
                gate_keithley_resource, 
                drain_range, 
                gate_range, 
                hardware_sweep, 
                integration_time, 
                current_compliance,
                set_measure_delay,
                experiment_name,
                measurement_name,
                measurement_count)


    def initialize_experiment(self):
        self.experiment = IV_Experiment()
        (measurement_type,
         drain_keithley_resource, 
         gate_keithley_resource, 
         drain_range, 
         gate_range, 
         hardware_sweep, 
         integration_time, 
         current_compliance,
         set_measure_delay,
         experiment_name,
         measurement_name,
         measurement_count) = self.__get_values_from_ui()

        
        self.experiment.init_hardware(drain_keithley_resource, gate_keithley_resource)
        self.experiment.prepare_experiment(measurement_type,
                                           gate_range,
                                           drain_range,
                                           hardware_sweep,
                                           integration_time,
                                           current_compliance,
                                           set_measure_delay)
        self.experiment.prepare_hardware()
        #exp.prepare_experiment(TRANSFER_MEASUREMENT,float_range(0,1.5,len=101),float_range(-1,1,len=5), True, INTEGRATION_MIDDLE, 0.001, 0.001)
        #exp.prepare_hardware()


    @QtCore.pyqtSlot()
    def on_startButton_clicked(self):
        print("start")
        self.initialize_experiment()
        self.experiment.start()
        

    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        print("stop")
        self.experiment.stop()
        
    def closeEvent(self,event):

        (measurement_type,
                drain_keithley_resource, 
                gate_keithley_resource, 
                drain_range, 
                gate_range, 
                hardware_sweep, 
                integration_time, 
                current_compliance,
                set_measure_delay,
                experiment_name,
                measurement_name,
                measurement_count) = self.__get_values_from_ui()

        config = configparser.RawConfigParser()
        section = MainView.config_file_section_name
        has_section = config.has_section(section)
        if not has_section:
            config.add_section(section)

        config[section] = {self.measurement_type_option: str(measurement_type),
                           self.drain_keithley_resource_option: str(drain_keithley_resource),
                            self.gate_keithley_resource_option: str(gate_keithley_resource),
                            self.drain_start_option: str(drain_range.start),
                            self.drain_stop_option: str(drain_range.stop),
                            self.drain_points_option : str(drain_range.length),
                            self.gate_start_option: str(gate_range.start),
                            self.gate_stop_option:str( gate_range.stop),
                            self.gate_points_option : str(gate_range.length),
                            self.hardware_sweep_option: str(hardware_sweep ),
                            self.integration_time_option: str(integration_time ),
                            self.set_measure_delay_option: str(set_measure_delay),
                            self.experiment_name_option: str(experiment_name),
                            self.measurement_name_option: str(measurement_name),
                            self.measurement_count_option: str(measurement_count),
                            self.working_directory_option: str(self.working_directory )}

        with open(self.config_filename,'w') as configfile:
            config.write(configfile)



if __name__== "__main__":
    #app = QtGui.QApplication(sys.argv)
    #app.setApplicationName("LegacyNoiseMeasurementSetup")
    ##app.setStyle("cleanlooks")

    ##css = "QLineEdit#sample_voltage_start {background-color: yellow}"
    ##app.setStyleSheet(css)
    ##sample_voltage_start

    #wnd = MainView()
    #wnd.show()
    exp = IV_Experiment()
    exp.init_hardware('GPIB0::5::INSTR', 'GPIB0::16::INSTR')
    exp.prepare_experiment(TRANSFER_MEASUREMENT,float_range(0,1.5,len=101),float_range(-1,1,len=5), True, INTEGRATION_MIDDLE, 0.001, 0.001)
    exp.prepare_hardware()
    exp.open_experiment("", "test_meas",1)
    exp.perform_measurement()
    #exp.start()
    
    #exp.stop()

    #exp.wait()
    #exp.perform_measurement()
    sys.exit(0)
    #sys.exit(app.exec_())

    
    
   