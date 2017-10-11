import sys
import os
import time
import numpy as np
import pyqtgraph as pg

from PyQt4 import uic, QtGui, QtCore

from keithley24xx import Keithley24XX

from range_handlers import float_range



pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', None) #'w')
pg.setConfigOption('foreground','k')

INTEGRATION_SPEEDS = ["Slow", "Middle", "Fast"]
INTEGRATION_SLOW,INTEGRATION_MIDDLE, INTEGRATION_FAST = INTEGRATION_SPEEDS

MEASUREMENT_TYPES = ["Output", "Transfer"]
OUTPUT_MEASUREMENT, TRANSFER_MEASUREMENT = MEASUREMENT_TYPES


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

        indep_device.SelectTraceBufferControl(Keithley24XX.NEXT_TRACE_CONTROL)
        dep_device.SelectTraceBufferControl(Keithley24XX.NEXT_TRACE_CONTROL)
        
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

    def _perform_hardware_sweep(self):
        
        if self.measurement_type == OUTPUT_MEASUREMENT:
            gate_range = self.gate_range
            drain_range = self.drain_range
            self.drain_keithley.OutputOn()
            self.gate_keithley.OutputOn()    
            for gate_voltage in np.linspace(gate_range.start, gate_range.stop, gate_range.length, True):
                self.gate_keithley.SetVoltageAmplitude(gate_voltage)
                
                self.drain_keithley.Initiate()
                self.gate_keithley.Initiate()
                
                self.drain_keithley.WaitOperationCompleted()
                self.gate_keithley.WaitOperationCompleted()
                
                strData = self.drain_keithley.ReadTraceData() #k.FetchData()
                strData2 = self.gate_keithley.ReadTraceData() #k2.FetchData()
                data = np.fromstring(strData, sep=',')
                data2 = np.fromstring(strData2, sep=',')
                data = data.reshape((drain_range.length,5)).T
                data2 = data2.reshape((drain_range.length,5)).T
    
                voltages, currents, resistances, times, status  = data
                voltages2, currents2, resistances2, times2, status2  = data2


                pg.plot(voltages, currents)
                pg.plot(voltages2, currents2)

            self.drain_keithley.OutputOn()
            self.gate_keithley.OutputOn()    

        elif self.measurement_type == TRANSFER_MEASUREMENT:
            pass

    def _perform_software_sweep(self):
        if self.measurement_type == OUTPUT_MEASUREMENT:
            pass
        elif self.measurement_type == TRANSFER_MEASUREMENT:
            pass

    def perform_measurement(self):
        if self.hardware_sweep:
            self._perform_hardware_sweep()
        else:
            self._perform_software_sweep()


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
    ##app.setStyle("cleanlooks")

    ##css = "QLineEdit#sample_voltage_start {background-color: yellow}"
    ##app.setStyleSheet(css)
    ##sample_voltage_start

    #wnd = MainView()
    #wnd.show()
    exp = IV_Experiment()
    exp.init_hardware('GPIB0::5::INSTR', 'GPIB0::16::INSTR')
    exp.prepare_experiment(OUTPUT_MEASUREMENT,float_range(0,1.5,len=5),float_range(-1,1,len=101), True, INTEGRATION_MIDDLE, 0.5, 0.001)
    exp.prepare_hardware()
    exp.perform_measurement()
    #sys.exit(0)
    sys.exit(app.exec_())

    
    
   