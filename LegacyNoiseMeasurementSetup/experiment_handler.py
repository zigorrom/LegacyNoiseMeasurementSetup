import sys
from nodes import ExperimentSettings, ValueRange, HardwareSettings
from configuration import Configuration
from hp34401a_multimeter import HP34401A,HP34401A_FUNCTIONS
from hp35670a_dsa import HP3567A, HP35670A_MODES,HP35670A_CALC, HP35670A_TRACES,HP35670A_INPUTS
from arduino_controller import ArduinoController
from motorized_potentiometer import MotorizedPotentiometer
import numpy as np
from n_enum import enum
from PyQt4 import QtCore





import pyqtgraph as pg
from multiprocessing.queues import JoinableQueue
from multiprocessing.context import Process
from multiprocessing import Event
from collections import deque
 


MeasurementTypes = enum("spectrum", "timetrace", "time_spectrum")

class DataHandler:  #(QtCore.QObject):
    #spectrum_updated_signal = QtCore.pyqtSignal(int, dict) # int - range, dict - data{f:frequency, d:data}
    #resulting_spectrum_updated_signal = QtCore.pyqtSignal(dict)
    #timetrace_updated_signal = QtCore.pyqtSignal(object)
    # should gether data and 
    # 1 - save to file
    # 2 - notify visualization
    #meas_ranges:
    #{0 - range number: (0 - start freq, 1600- end freq, 1 - freq step) - list of params }
    def _get_frequencies(self, spectrum_ranges):
        result = {}
        for k,v in spectrum_ranges.items():
            start,stop,step = v
            nlines = 1+(stop-start)/step
            result[k] = np.linspace(start,stop, nlines, True)
        return result

    def __init__(self, working_directory, measurement_type = MeasurementTypes.spectrum, spectrum_ranges = {0: (0,1600,1),1:(0,102400,64)}, parent = None, input_data_queue = None):
        #super().__init__(parent)
        #assert isinstance(measurement_type, type(MeasurementTypes))
        self._input_data_queue = None
        if input_data_queue:
            assert isinstance(input_data_queue, JoinableQueue)
            self._input_data_queue = input_data_queue
    
        assert isinstance(working_directory, str)
        self._working_directory = working_directory


        self._spectrum_ranges = spectrum_ranges
        self._frequencies = self._get_frequencies(spectrum_ranges)
        self._spectrum_data = {}   


        self._measured_temp_start = 0;
        self._measured_temp_end = 0;

        self._measured_main_voltage_start = 0;
        self._measured_main_voltage_end = 0;

        self._measured_sample_voltage_start = 0;
        self._measured_sample_voltage_end = 0;
        
        self._measured_gate_voltage_start = 0;
        self._measured_gate_voltage_end = 0;

        self._sample_current_start = 0;
        self._sample_current_end = 0;

        self._sample_resistance_start = 0;
        self._sample_resistance_end = 0;

        self._equivalent_resistance_start = 0;
        self._equivalent_resistance_end = 0;
        



    @property
    def start_temperature(self):
        return self._measured_temp_start
    
    @start_temperature.setter
    def start_temperature(self, value):
        self._measured_temp_start = value

    @property
    def end_temperature(self):
        return self._measured_temp_end
    
    @end_temperature.setter
    def end_temperature(self, value):
        self._measured_temp_end = value

    @property
    def start_main_voltage(self):
        return self._measured_main_voltage_start
    
    @start_main_voltage.setter
    def start_main_voltage(self, value):
        self._measured_main_voltage_start = value

    @property
    def end_main_voltage(self):
        return self._measured_main_voltage_end
    
    @end_main_voltage.setter
    def end_main_voltage(self, value):
        self._measured_main_voltage_end = value

    @property
    def start_sample_voltage(self):
        return self._measured_sample_voltage_start
    
    @start_sample_voltage.setter
    def start_sample_voltage(self, value):
        self._measured_sample_voltage_start = value

    @property
    def end_sample_voltage(self):
        return self._measured_sample_voltage_start
    
    @end_sample_voltage.setter
    def end_sample_voltage(self, value):
        self._measured_sample_voltage_start = value


    def update_spectrum(self, data,range = 0):
        #range numeration from 0:   0 - 0 to 1600HZ
        #                           1 - 0 to 102,4KHZ
        self._spectrum_data[range] = data
        q = self._input_data_queue
        if q:
            q.put_nowait(range, {'f':self._frequencies[range],'d':data})
        
            
        #emit(range, {'f':self._frequencies[range],'d':data})
        
    def update_resulting_spectrum(self):
        
              
        pass


    def update_timetrace(self,data):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

class ProcessingThread(QtCore.QThread):
    threadStarted = QtCore.pyqtSignal()
    threadStopped = QtCore.pyqtSignal()

    def __init__(self, input_data_queue = None,visualization_queue = None, parent = None):
        super().__init__(parent)
        self.alive = False
        assert isinstance(visualization_queue, deque)
        self._visualization_queue = visualization_queue
        assert isinstance(input_data_queue, JoinableQueue)
        self._input_data_queue = input_data_queue


    def stop(self):
        self.alive = False
        self.wait()

    def run(self):
        self.alive = True
        #while self.alive
        while self.alive or (not self._input_data_queue.empty()):
            try:
                data = self._input_data_queue.get(timeout = 1)
                self._input_data_queue.task_done()
                self._visualization_queue.appendleft(data)
            except EOFError as e:
                print(str(e))
                break
            except:
                pass

        self.alive = False


class Experiment(Process):
    def __init__(self, input_data_queue = None, simulate = True):
        #self.__hardware_settings = None
        #self.__exp_settings = ExperimentSettings()
        #self.__initialize_hardware()
        super().__init__()

        self._simulate = simulate

        self.exit = Event()

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

        self._counter = 0

        self._data_handler = DataHandler(working_directory = "",input_data_queue = input_data_queue)


    def initialize_settings(self, configuration):
        assert isinstance(configuration, Configuration)
        self.__config = configuration
        self.__exp_settings = configuration.get_node_from_path("Settings.ExperimentSettings")
        assert isinstance(self.__exp_settings, ExperimentSettings)
        self.__hardware_settings = configuration.get_node_from_path("Settings.HardwareSettings")
        assert isinstance(self.__hardware_settings, HardwareSettings)
        
        if not self._simulate:
            self.__initialize_hardware();

    def __initialize_hardware(self):
        self.__dynamic_signal_analyzer = HP3567A(self.__hardware_settings.dsa_resource)
        self.__arduino_controller = ArduinoController(self.__hardware_settings.arduino_controller_resource)
        self.__sample_multimeter = HP34401A(self.__hardware_settings.sample_multimeter_resource)
        self.__main_gate_multimeter = HP34401A(self.__hardware_settings.main_gate_multimeter_resource)
        assert self.__dynamic_signal_analyzer and self.__arduino_controller and self.__sample_multimeter and self.__main_gate_multimeter


    def get_meas_ranges(self):
        fg_range = self.__config.get_node_from_path("front_gate_range")
        if self.__exp_settings.use_set_vfg_range:
            assert isinstance(fg_range, ValueRange)
        ds_range = self.__config.get_node_from_path("drain_source_range")
        if self.__exp_settings.use_set_vds_range:
            assert isinstance(fg_range, ValueRange)
        return ds_range, fg_range

    def output_curve_measurement_function(self):
        ds_range, fg_range = self.get_meas_ranges()
        
        if (not self.__exp_settings.use_set_vfg_range) and (not self.__exp_settings.use_set_vds_range):
            self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)


        elif self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            for vfg in fg_range.get_range_handler():
                for vds in ds_range.get_range_handler():
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in ds_range.get_range_handler():
                    self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
            for vfg in fg_range.get_range_handler():
                   self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            raise ValueError("range handlers are not properly defined")
        #    self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        #foreach vfg_voltage in Vfg_range 
        #    foreach vds_voltage in Vds_range
        #       single_value_measurement(vds_voltage,vfg_voltage)
        

    def transfer_curve_measurement_function(self):
        ds_range, fg_range = self.get_meas_ranges()
        if (not self.__exp_settings.use_set_vds_range) and (not self.__exp_settings.use_set_vfg_range):
             self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        elif self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            
            for vds in ds_range.get_range_handler():
                for vfg in fg_range.get_range_handler():
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in ds_range.get_range_handler():
                    self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
             for vfg in fg_range.get_range_handler():
                    self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            raise ValueError("range handlers are not properly defined")
        #    self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        # foreach vds_voltage in Vds_range
        #     foreach vfg_voltage in Vfg_range 
        #       single_value_measurement(vds_voltage,vfg_voltage)
    def switch_transistor(self,transistor):
        if self._simulate:
            print("simulating switching transistor to {0}".format (transistor))
            return
        pass

    def set_front_gate_voltage(self,voltage):
        if self._simulate:
            print("simulate settign front gate voltage: {0}".format(voltage))
            return 

        print("settign front gate voltage: {0}".format(voltage))
        channel = self.__hardware_settings.gate_potentiometer_channel
        potentiometer = MotorizedPotentiometer(self.__arduino_controller, channel, self.__main_gate_multimeter)
        potentiometer.set_voltage(voltage)



    def set_drain_source_voltage(self,voltage):
        if self._simulate:
            print("simulating settign drain source voltage: {0}".format(voltage))
            return
        
        print("settign drain source voltage: {0}".format(voltage))
        print("settign front gate voltage: {0}".format(voltage))
        channel = self.__hardware_settings.sample_potentiometer_channel
        potentiometer = MotorizedPotentiometer(self.__arduino_controller, channel, self.__sample_multimeter)
        potentiometer.set_voltage(voltage)
    #def set_voltage(self, voltage):
    #    pass   

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
        
        print(self.__exp_settings.meas_gated_structure)
        print(self.__exp_settings.meas_characteristic_type)
        print(self.__exp_settings.use_transistor_selector)
       
        if not self.__exp_settings.meas_gated_structure:# non gated structure measurement
            func = self.non_gated_structure_meaurement_function
        elif self.__exp_settings.meas_characteristic_type == 0: #output curve
            func = self.output_curve_measurement_function
        elif self.__exp_settings.meas_characteristic_type == 1: #transfer curve
            func = self.transfer_curve_measurement_function
        else: 
            raise AssertionError("function was not selected properly")

        if self.__exp_settings.use_transistor_selector:
            def execution_function(self):
                for transistor in self.__exp_settings.transistor_list:
                    self.switch_transistor(transistor)
                    func(self)
            return execution_function

        return func



    def perform_non_gated_single_measurement(self):
        raise NotImplementedError()
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
        self._counter+=1
        print("count: {0}".format(self._counter))
        #pass
        
    def __initialize_analyzer(self,analyzer):
        #analyzer = self.__dynamic_signal_analyzer
        analyzer.remove_time_capture_data()
        analyzer.clear_status()

        #set mode
        analyzer.select_instrument_mode(HP35670A_MODES.FFT)
        analyzer.switch_input(HP35670A_INPUTS.INP2, False)
        analyzer.select_active_traces(HP35670A_CALC.CALC1, HP35670A_TRACES.A)
        analyzer.select_real_format(64)
        analyzer.select_ascii_format()
        analyzer.select_power_spectrum_function(HP35670A_CALC.CALC1)
        analyzer.select_voltage_unit(HP35670A_CALC.CALC1)
        analyzer.switch_calibration(False)
        analyzer.set_frequency_resolution(1600)
        analyzer.set_source_voltage(5)
        #calibrate
        if self.__exp_settings.calibrate_before_measurement:
            analyzer.calibrate()
        
        #set averaging
        analyzer.switch_averaging(True)
        analyzer.set_average_count(self.__exp_settings.averages)
        analyzer.set_display_update_rate(self.__exp_settings.display_refresh)
        #set overload_rejection
        analyzer.switch_overload_rejection(self.__exp_settings.overload_rejecion)
        
        
        analyzer.set_frequency_start(0)
        analyzer.set_frequency_stop(1600)
        return analyzer

    def perform_single_measurement(self):
        if self._simulate:
            print("simulating experiment")
            data = 10**-9 * np.random.random(1600)
            self._data_handler.update_spectrum(data,0)
            return

        analyzer = self.__initialize_analyzer(self.__dynamic_signal_analyzer)



        #measure_temperature
        #measure Vds, Vfg
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #measure spectra 
        print(analyzer.get_points_number(HP35670A_CALC.CALC1))
        analyzer.init_instrument()

        analyzer.wait_operation_complete()
        
        str_data = analyzer.get_data(HP35670A_CALC.CALC1)
        data = np.fromstring(str_data, sep = ',')
        self._data_handler.update_spectrum(data)

        #measure Vds, Vfg
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #calculate resulting spectra
        #write data to measurement file and experiment file
        print("performing perform_single_measurement")
        self._counter+=1
        print("count: {0}".format(self._counter))
        #pass


    def perform_experiment(self):
        function_to_execute = self.generate_experiment_function()
        function_to_execute()


    def stop(self):
        self.exit.set()

    def run(self):
        sys.stdout = open("log.txt", "w")
        cfg = Configuration()
        self.initialize_settings(cfg)
        self.perform_experiment()


if __name__ == "__main__":
    
    #settings = cfg.get_node_from_path("Settings.ExperimentSettings")
    #assert isinstance(settings, ExperimentSettings)
    #print(settings)

    cfg = Configuration()
    exp = Experiment()
    exp.initialize_settings(cfg)
    exp.perform_experiment()
    #exp.start()

    #exp.join()



    #h = DataHandler(MeasurementTypes.spectrum)
    #data = np.random.random(1601)
    #h.update_spectrum(data,0)

   

    #visual = pg.GraphicsLayoutWidget()
    #s = SpectrumPlotWidget(visual)
    #visual.show()

    pass