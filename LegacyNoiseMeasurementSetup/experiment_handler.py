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
from os.path import join

import pyqtgraph as pg
from multiprocessing import JoinableQueue
from multiprocessing import Process
from multiprocessing import Event
import multiprocessing
from collections import deque
from plot import SpectrumPlotWidget
import time
import math

from measurement_data_structures import MeasurementInfo
from experiment_writer import ExperimentWriter

class ExperimentController(QtCore.QObject):
    def __init__(self, spectrum_plot=None, timetrace_plot=None, status_object = None, measurement_ranges = {0: (0,1600,1),1:(0,102400,64)},  parent = None):
        super().__init__(parent)
        if spectrum_plot:
            assert isinstance(spectrum_plot, SpectrumPlotWidget)
        self._spectrum_plot = spectrum_plot
        #self._spectrum_plot
        self._running = False

        self._visualization_deque = deque(maxlen = 100)
        self._input_data_queue = JoinableQueue()

        self._status_object = status_object

        ## pass configuration to threads

        self._processing_thread = None # ProcessingThread(self._input_data_queue, self._visualization_deque)
        self._experiment_thread = None # Experiment(self._input_data_queue)

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setInterval(20)
        self._refresh_timer.timeout.connect(self._update_gui)
        self._counter = 0

    def __init_process_thread(self):
        self._processing_thread = ProcessingThread(self._input_data_queue, self._visualization_deque)
        self._processing_thread.experimentStarted.connect(self._on_experiment_started)
        self._processing_thread.experimentFinished.connect(self._on_experiment_finished)
        self._processing_thread.measurementStarted.connect(self._on_measurement_started)
        self._processing_thread.measurementFinished.connect(self._on_measurement_finished)
        self._processing_thread.measurementDataArrived.connect(self._on_measurement_info_arrived)
        self._processing_thread.commandReceived.connect(self._command_received)

    def __init_experiment_thread(self):
        self._experiment_thread = ExperimentHandler(self._input_data_queue) #ExperimentProcess(self._input_data_queue,True)

    def _command_received(self,cmd):
        self._status_object.send_message("Command received: {0}".format(ExperimentCommands[cmd]))

    def _on_experiment_started(self, params): #experiment_name = "", **kwargs):
        
        experiment_name = params.get("experiment_name")
        msg = "Experiment \"{0}\" started".format(experiment_name)
        print(msg)
        self._status_object.send_message(msg)
        self._status_object.send_multiple_param_changed(params)
        
        #print(experiment_name)
        #print(kwargs)
        #print(**params)
        #msg = "Experiment \"{0}\" started".format(experiment_name)
        #print(msg)
        #self._status_object.send_message(msg)
        #self._status_object.send_value_changed("experiment_name", experiment_name)
    #def _on_experiment_started(self, experiment_name = ""):
    #    msg = "Experiment \"{0}\" started".format(experiment_name)
    #    print(msg)
    #    self._status_object.send_message(msg)
    #    self._status_object.send_value_changed("experiment_name", experiment_name)

    def _on_experiment_finished(self):
        print("Experiment finished")
        self.stop()

    def _on_measurement_started(self,  params):
        measurement_name = params.get("measurement_name")
        measurement_count = params.get("measurement_count")
        msg = "Measurement \"{0}:{1}\" started".format(measurement_name, measurement_count)
        print(msg)
        self._status_object.send_message(msg)
        self._status_object.send_multiple_param_changed(params)

    #def _on_measurement_started(self, measurement_name = "", measurement_count = 1):
    #    msg = "Measurement \"{0}\" started".format(measurement_name)
    #    print(msg)
    #    self._status_object.send_message(msg)
    #    self._status_object.send_multiple_param_changed({"measurement_name":measurement_name, "measurement_count": measurement_count})
        #self._status_object.send_value_changed("measurement_name", measurement_name)

    def _on_measurement_finished(self):
        print("Measurement finished")

    def _on_measurement_info_arrived(self,measurement_info):
        print("measurement_info_arrived")
        self._status_object.send_measurement_info_changed(measurement_info)
        #if isinstance(data_dict, dict):
        #    for k,v in data_dict.items():
                #self._status_object.send_value_changed(k,v)

    def _update_gui(self):
        try:
            #print("refreshing: {0}".format(self._counter))
            self._counter+=1
            data = self._visualization_deque.popleft()
            cmd_format = "{0} command received"

            cmd = data.get('c')
            #print(cmd_format.format(ExperimentCommands[cmd]))
            
            if cmd is ExperimentCommands.DATA:
                index = data['i']
                rang = data['r']
                #print("visualized data index: {0}".format(index))
                self._spectrum_plot.update_spectrum(rang ,data)
            
        except Exception as e:
            print(str(e))

    def start(self):
        if self._running:
            return
        self.__init_process_thread()
        self.__init_experiment_thread()
        self._refresh_timer.start()
        self._experiment_thread.start()
        self._processing_thread.start()
        self._running = True

    def stop(self):
        if not self._running:
            return
        self._refresh_timer.stop()
        self._experiment_thread.stop()
        self._experiment_thread.join()
        self._input_data_queue.join()
        self._processing_thread.stop()
        self._running = False

class ProcessingThread(QtCore.QThread):
    
    threadStarted = QtCore.pyqtSignal()
    threadStopped = QtCore.pyqtSignal()
    commandReceived = QtCore.pyqtSignal(int)
    experimentStarted = QtCore.pyqtSignal(dict)
    experimentFinished = QtCore.pyqtSignal()
    measurementStarted = QtCore.pyqtSignal(dict)
    measurementFinished = QtCore.pyqtSignal()
    measurementDataArrived = QtCore.pyqtSignal(MeasurementInfo)

    def __init__(self, input_data_queue = None,visualization_queue = None, parent = None):
        super().__init__(parent)
        self.alive = False
        assert isinstance(visualization_queue, deque)
        self._visualization_queue = visualization_queue
        #assert isinstance(input_data_queue, JoinableQueue)
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
                cmd_format = "{0} command received"
                cmd = data.get('c')
                param = data.get('p')
                
                #print(cmd_format.format(ExperimentCommands[cmd]))
                if cmd is None:
                    continue
                elif cmd is ExperimentCommands.EXPERIMENT_STARTED:
                    self.commandReceived.emit(ExperimentCommands.EXPERIMENT_STARTED)
                    self.experimentStarted.emit(param)
                    continue

                elif cmd is ExperimentCommands.EXPERIMENT_STOPPED:
                    self.alive = False
                    self.commandReceived.emit(ExperimentCommands.EXPERIMENT_STOPPED)
                    self.experimentFinished.emit()
                    break

                elif cmd is ExperimentCommands.MEASUREMENT_STARTED:
                    self.commandReceived.emit(ExperimentCommands.MEASUREMENT_STARTED)
                    self.measurementStarted.emit(param)
                    continue

                elif cmd is ExperimentCommands.MEASUREMENT_FINISHED:
                    self.commandReceived.emit(ExperimentCommands.MEASUREMENT_FINISHED)
                    self.measurementFinished.emit()
                    continue

                elif cmd is ExperimentCommands.MEASUREMENT_INFO:
                    self.measurementDataArrived.emit(param)

                elif cmd is ExperimentCommands.DATA:
                    self._visualization_queue.append(data)    

            except EOFError as e:
                print(str(e))
                break
            except:
                pass

        self.alive = False

ExperimentCommands = enum("EXPERIMENT_STARTED","EXPERIMENT_STOPPED","DATA","MESSAGE", "MEASUREMENT_STARTED", "MEASUREMENT_FINISHED", "SPECTRUM_DATA", "TIMETRACE_DATA","EXPERIMENT_INFO", "MEASUREMENT_INFO", "ABORT", "ERROR")
MeasurementTypes = enum("spectrum", "timetrace", "time_spectrum")



class ExperimentHandler(Process):
    def __init__(self, input_data_queue = None):
        super().__init__()
        self._exit = Event()
        self._experiment  = None
        self._input_data_queue = input_data_queue

    def stop(self):
        self._exit.set()

    def run(self):
        sys.stdout = open("log.txt", "w")
        cfg = Configuration()
        exp_settings = cfg.get_node_from_path("Settings.ExperimentSettings")
        assert isinstance(exp_settings, ExperimentSettings)
        simulate = exp_settings.simulate_experiment

        if simulate:
            self._experiment = SimulateExperiment(self._input_data_queue, self._exit)
        else:
            self._experiment = PerformExperiment(self._input_data_queue, self._exit)
        
        self._experiment.initialize_settings(cfg)
        self._experiment.initialize_hardware()
        self._experiment.perform_experiment()

class Measurement:
    def __init__(self):
        pass

    def new_measurement(self):
        pass

    

class Experiment:
    def __init__(self, simulate = False, input_data_queue = None, stop_event = None):
        self.__config = None
        self.__exp_settings = None
        self.__hardware_settings = None
        self._simulate = simulate
        self._execution_function = None
        self._input_data_queue = input_data_queue
        self._working_directory = ""
        self._data_handler = None
        self._stop_event = stop_event
        self._measurement_info = None
        self._spectrum_ranges = {0: (1,1600,1),1:(64,102400,64)}
        self._spectrum_linking_frequencies = {0:(1,1600),1:(1600,102400)}
        self._frequencies = self._get_frequencies(self._spectrum_ranges)
        self._frequency_indexes = self._get_frequency_linking_indexes(self._spectrum_ranges, self._spectrum_linking_frequencies)
        self._spectrum_data = {}
        self._measurement_counter = 0
        self._experiment_writer = None                                                                                                                                         
    
    @property
    def need_exit(self):
        if self._stop_event:
            return self._stop_event.is_set()
        return False

    @property
    def configuration(self):
        return self.__config

    @property
    def experiment_settings(self):
        return self.__exp_settings 

    @property
    def hardware_settings(self):
        return self.__hardware_settings

    @property
    def simulate(self):
        return self._simulate

    #@property
    #def data_handler(self):
    #    return self._data_handler
    def _get_frequencies(self, spectrum_ranges):
        result = {}
        for k,v in spectrum_ranges.items():
            start,stop,step = v
            nlines = 1+(stop-start)/step
            result[k] = np.linspace(start,stop, nlines, True)
        return result

    def _get_frequency_linking_indexes(self, spectrum_ranges, linking_frequencies):
        result = {}
        for rng, vals in spectrum_ranges.items():
            start,stop,step = vals
            start_freq, stop_freq = linking_frequencies[rng]
            start_freq_idx =  math.ceil(start_freq/step)
            stop_freq_idx = math.floor(stop_freq/step)
            result[rng] = (start_freq_idx, stop_freq_idx)
        return result


    def initialize_settings(self, configuration):
        self.__config = configuration
        assert isinstance(configuration, Configuration)
        self.__exp_settings = configuration.get_node_from_path("Settings.ExperimentSettings")
        assert isinstance(self.__exp_settings, ExperimentSettings)
        self.__hardware_settings = configuration.get_node_from_path("Settings.HardwareSettings")
        assert isinstance(self.__hardware_settings, HardwareSettings)
        self._working_directory = self.__exp_settings.working_directory
        
        #self._data_handler = DataHandler(self._working_directory,input_data_queue = self._input_data_queue)

    def initialize_hardware(self):
        if self.__exp_settings.use_transistor_selector or self.__exp_settings.use_automated_voltage_control:
            self.__arduino_controller = ArduinoController(self.__hardware_settings.arduino_controller_resource)

        self.__dynamic_signal_analyzer = HP3567A(self.__hardware_settings.dsa_resource)
        self.__sample_multimeter = HP34401A(self.__hardware_settings.sample_multimeter_resource)
        self.__main_gate_multimeter = HP34401A(self.__hardware_settings.main_gate_multimeter_resource)
    

   

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
        
        if (not self.__exp_settings.use_set_vfg_range) and (not self.__exp_settings.use_set_vds_range) and not self.need_exit:
            self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        elif self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range and not self.need_exit:
            for vfg in fg_range.get_range_handler():
                if self.need_exit:
                    return
                for vds in ds_range.get_range_handler():
                    if self.need_exit:
                        return
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in ds_range.get_range_handler():
                if self.need_exit:
                    return
                self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
            for vfg in fg_range.get_range_handler():
                if self.need_exit:
                    return
                self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            raise ValueError("range handlers are not properly defined")


    def transfer_curve_measurement_function(self):
        ds_range, fg_range = self.get_meas_ranges()
        if (not self.__exp_settings.use_set_vds_range) and (not self.__exp_settings.use_set_vfg_range) and not self.need_exit:
             self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        elif self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            for vds in ds_range.get_range_handler():
                if self.need_exit:
                    return
                for vfg in fg_range.get_range_handler():
                    if self.need_exit:
                        return
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in ds_range.get_range_handler():
                if self.need_exit:
                    return
                self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
             for vfg in fg_range.get_range_handler():
                 if self.need_exit:
                    return
                 self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            raise ValueError("range handlers are not properly defined")

    def non_gated_structure_meaurement_function(self):
        if self.__exp_settings.use_set_vds_range:
             for vds in self.__exp_settings.vds_range:
                 if self.need_exit:
                    return
                 self.non_gated_single_value_measurement(vds)
        else:
            self.non_gated_single_value_measurement(self.__exp_settings.drain_source_voltage)

    def switch_transistor(self,transistor):
        raise NotImplementedError()

    def set_front_gate_voltage(self,voltage):
        raise NotImplementedError()

    def set_drain_source_voltage(self,voltage):
        raise NotImplementedError()

    def single_value_measurement(self, drain_source_voltage, gate_voltage):
        raise NotImplementedError()

    def non_gated_single_value_measurement(self, drain_source_voltage):
        raise NotImplementedError()

    def _send_command(self,command):
        q = self._input_data_queue
        if q:
            q.put_nowait({'c': command})

    def _send_command_with_param(self,command,param):
        q = self._input_data_queue
        if q:
            q.put_nowait({'c':command, 'p':param})

    def _send_command_with_params(self,command, **kwargs):
        q = self._input_data_queue
        params = {'c': command}
        if kwargs:
            params['p'] = kwargs
        #params.update(kwargs)
        if q:
            q.put_nowait(params)   


    def open_experiment(self):
        experiment_name = self.__exp_settings.experiment_name
        self._send_command_with_params(ExperimentCommands.EXPERIMENT_STARTED, experiment_name = experiment_name)
        self._measurement_counter = self.__exp_settings.measurement_count
        self._experiment_writer = ExperimentWriter(self._working_directory)
        self._experiment_writer.open_experiment(experiment_name)


    def close_experiment(self):
        self._send_command(ExperimentCommands.EXPERIMENT_STOPPED)
        self._experiment_writer.close_experiment()

    def open_measurement(self):
        #print("simulate open measurement")
        measurement_name = self.__exp_settings.measurement_name
        measurement_counter = self._measurement_counter
        self._measurement_info = MeasurementInfo(measurement_name, measurement_counter)
        self._send_command_with_params(ExperimentCommands.MEASUREMENT_STARTED, measurement_name = measurement_name, measurement_count = measurement_counter) 

        self._experiment_writer.open_measurement(measurement_name,measurement_counter)

    def close_measurement(self):
        #print("simulate close measurement")
        self._measurement_counter+=1
        self._send_command(ExperimentCommands.MEASUREMENT_FINISHED)
        self._spectrum_data = dict()
        

        self._experiment_writer.close_measurement()

    def send_measurement_info(self):
        self._send_command_with_param(ExperimentCommands.MEASUREMENT_INFO, self._measurement_info)

    def update_spectrum(self, data,rang = 0, averages = 1):
        #range numeration from 0:   0 - 0 to 1600HZ
        #                           1 - 0 to 102,4KHZ
        current_data_dict = self._spectrum_data.get(rang)
        average_data = data
        if not current_data_dict:
            self._spectrum_data[rang] = {"avg": averages,"d": data}
        else:
            current_average = current_data_dict["avg"]
            current_data = current_data_dict["d"]
            #self.average = np.average((self.average, data['p']), axis=0, weights=(self.average_counter - 1, 1))

            average_data = np.average((current_data, data),axis = 0, weights = (current_average, averages))
            current_average += averages

            self._spectrum_data[rang] = {"avg": current_average,"d": average_data}
             
        #self._spectrum_data[rang] = data
        q = self._input_data_queue
        freq = self._frequencies[rang] 
        
        result = {'c': ExperimentCommands.DATA, 'r': rang, 'f': freq, 'd':average_data, 'i': 1}#data, 'i': 1}
        if q:
            q.put_nowait(result) 

    def get_resulting_spectrum(self):
        list_of_spectrum_slices = []
        list_of_frequency_slices= []
        for rng, spectrum_data in self._spectrum_data.items():
            start_idx, stop_idx = self._frequency_indexes[rng]
            data = spectrum_data["d"][start_idx:stop_idx]
            freq = self._frequencies[rng][start_idx:stop_idx]
            list_of_spectrum_slices.append(data)
            list_of_frequency_slices.append(freq)
        
        #frequencies = np.vstack(

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
            self._execution_function = execution_function
        self._execution_function = func
        
    def perform_experiment(self):
        self.generate_experiment_function()
        self.open_experiment()
        self._execution_function()
        self.close_experiment()

class SimulateExperiment(Experiment):
    def __init__(self, input_data_queue = None, stop_event = None):
        Experiment.__init__(self,True, input_data_queue, stop_event)

    def initialize_hardware(self):
        print("simulating hardware init")

    def switch_transistor(self, transistor):
        print("simulating switch transistor")

    def set_front_gate_voltage(self, voltage):
        print("simulate setting fg voltage: {0}".format(voltage))
    
    def set_drain_source_voltage(self, voltage):
        print("simulate setting ds voltage: {0}".format(voltage))

    def single_value_measurement(self, drain_source_voltage, gate_voltage):
        self.open_measurement()
        print("simulating single measurement vds:{0} vg:{1}".format(drain_source_voltage, gate_voltage))
        self.send_measurement_info()

        counter = 0
        max_counter = 100
        
        while counter < max_counter: #(not need_exit()) and counter < max_counter:
            data = 10**-9 * np.random.random(1600)
            self.update_spectrum(data,0)
            self.update_spectrum(data,1)
            counter+=1
            time.sleep(0.02)
        
        self.get_resulting_spectrum()
        self.send_measurement_info()
        self.close_measurement()

    def non_gated_single_value_measurement(self, drain_source_voltage):
        self.open_measurement()
        print("simulating non gated single measurement vds:{0}".format(drain_source_voltage))
        self.close_measurement()

class PerformExperiment(Experiment):
    def __init__(self, input_data_queue = None, stop_event = None):
        Experiment.__init__(self,False, input_data_queue, stop_event)

    def initialize_hardware(self):
        pass

    def switch_transistor(self, transistor):
        print("performing switch transistor")

    def set_front_gate_voltage(self, voltage):
        print("performing setting fg voltage: {0}".format(voltage))
    
    def set_drain_source_voltage(self, voltage):
        print("performing setting ds voltage: {0}".format(voltage))

    def single_value_measurement(self, drain_source_voltage, gate_voltage):
        self.open_measurement()
        print("performing single measurement")
        self.close_measurement()

    def non_gated_single_value_measurement(self, drain_source_voltage):
        self.open_measurement()
        print("performing non gated single measurement")
        self.close_measurement()




if __name__ == "__main__":
    
    cfg = Configuration()
    exp = SimulateExperiment(None,None)
    exp.initialize_settings(cfg)
    exp.initialize_hardware()

    exp.perform_experiment()

    #cfg = Configuration()
    #exp = ExperimentProcess(simulate = True)
    #exp.initialize_settings(cfg)
    #exp.perform_experiment()
    


    ##########################
    ##OLD version
    ##########################
    #class ExperimentProcess(Process):
    #def __init__(self, input_data_queue = None, simulate = True):
    #    super().__init__()
    #    self._simulate = simulate

    #    self.exit = Event()

    #    self._measured_temp_start = 0;
    #    self._measured_temp_end = 0;

    #    self._measured_main_voltage_start = 0;
    #    self._measured_main_voltage_end = 0;

    #    self._measured_sample_voltage_start = 0;
    #    self._measured_samole_voltage_end = 0;
        
    #    self._measured_gate_voltage_start = 0;
    #    self._measured_gate_voltage_end = 0;

    #    self._sample_current_start = 0;
    #    self._sample_current_end = 0;

    #    self._sample_resistance_start = 0;
    #    self._sample_resistance_end = 0;

    #    self._equivalent_resistance_start = 0;
    #    self._equivalent_resistance_end = 0;

    #    self._counter = 0

    #    self._data_handler = DataHandler(working_directory = "",input_data_queue = input_data_queue)

    #def initialize_settings(self, configuration):
    #    assert isinstance(configuration, Configuration)
    #    self.__config = configuration
    #    self.__exp_settings = configuration.get_node_from_path("Settings.ExperimentSettings")
    #    assert isinstance(self.__exp_settings, ExperimentSettings)
    #    self.__hardware_settings = configuration.get_node_from_path("Settings.HardwareSettings")
    #    assert isinstance(self.__hardware_settings, HardwareSettings)
        
    #    if not self._simulate:
    #        self.__initialize_hardware();

    #def __initialize_hardware(self):
    #    self.__dynamic_signal_analyzer = HP3567A(self.__hardware_settings.dsa_resource)
    #    self.__arduino_controller = ArduinoController(self.__hardware_settings.arduino_controller_resource)
    #    self.__sample_multimeter = HP34401A(self.__hardware_settings.sample_multimeter_resource)
    #    self.__main_gate_multimeter = HP34401A(self.__hardware_settings.main_gate_multimeter_resource)
    #    assert self.__dynamic_signal_analyzer and self.__arduino_controller and self.__sample_multimeter and self.__main_gate_multimeter

    #def get_meas_ranges(self):
    #    fg_range = self.__config.get_node_from_path("front_gate_range")
    #    if self.__exp_settings.use_set_vfg_range:
    #        assert isinstance(fg_range, ValueRange)
    #    ds_range = self.__config.get_node_from_path("drain_source_range")
    #    if self.__exp_settings.use_set_vds_range:
    #        assert isinstance(fg_range, ValueRange)
    #    return ds_range, fg_range

    #def output_curve_measurement_function(self):
    #    ds_range, fg_range = self.get_meas_ranges()
        
    #    if (not self.__exp_settings.use_set_vfg_range) and (not self.__exp_settings.use_set_vds_range):
    #        self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)


    #    elif self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
    #        for vfg in fg_range.get_range_handler():
    #            for vds in ds_range.get_range_handler():
    #                self.single_value_measurement(vds, vfg)
           
    #    elif not self.__exp_settings.use_set_vfg_range:
    #        for vds in ds_range.get_range_handler():
    #                self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
    #    elif not self.__exp_settings.use_set_vds_range:
    #        for vfg in fg_range.get_range_handler():
    #               self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
    #    else:
    #        raise ValueError("range handlers are not properly defined")
        

    #def transfer_curve_measurement_function(self):
    #    ds_range, fg_range = self.get_meas_ranges()
    #    if (not self.__exp_settings.use_set_vds_range) and (not self.__exp_settings.use_set_vfg_range):
    #         self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

    #    elif self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            
    #        for vds in ds_range.get_range_handler():
    #            for vfg in fg_range.get_range_handler():
    #                self.single_value_measurement(vds, vfg)
           
    #    elif not self.__exp_settings.use_set_vfg_range:
    #        for vds in ds_range.get_range_handler():
    #                self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
    #    elif not self.__exp_settings.use_set_vds_range:
    #         for vfg in fg_range.get_range_handler():
    #                self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
    #    else:
    #        raise ValueError("range handlers are not properly defined")
    #    #    self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

    #    # foreach vds_voltage in Vds_range
    #    #     foreach vfg_voltage in Vfg_range 
    #    #       single_value_measurement(vds_voltage,vfg_voltage)

    #def switch_transistor(self,transistor):
    #    if self._simulate:
    #        print("simulating switching transistor to {0}".format (transistor))
    #        return
    #    pass

    #def set_front_gate_voltage(self,voltage):
    #    if self._simulate:
    #        print("simulate settign front gate voltage: {0}".format(voltage))
    #        return 

    #    print("settign front gate voltage: {0}".format(voltage))
    #    channel = self.__hardware_settings.gate_potentiometer_channel
    #    potentiometer = MotorizedPotentiometer(self.__arduino_controller, channel, self.__main_gate_multimeter)
    #    potentiometer.set_voltage(voltage)



    #def set_drain_source_voltage(self,voltage):
    #    if self._simulate:
    #        print("simulating settign drain source voltage: {0}".format(voltage))
    #        return
        
    #    print("settign drain source voltage: {0}".format(voltage))
    #    print("settign front gate voltage: {0}".format(voltage))
    #    channel = self.__hardware_settings.sample_potentiometer_channel
    #    potentiometer = MotorizedPotentiometer(self.__arduino_controller, channel, self.__sample_multimeter)
    #    potentiometer.set_voltage(voltage)
    ##def set_voltage(self, voltage):
    ##    pass   

    #def single_value_measurement(self, drain_source_voltage, gate_voltage):
    #    #self.set_drain_source_voltage(drain_source_voltage)
    #    #self.set_front_gate_voltage(gate_voltage)
    #    #self.set_drain_source_voltage(drain_source_voltage) ## specifics of the circuit!!! to correct the value of dropped voltage on opened channel
    #    self.perform_single_measurement()
    #    #set vds_voltage
    #    # set vfg voltage
    #    # stabilize voltage
    #    # perform_single_measurement()
        

    #def non_gated_structure_meaurement_function(self):
    #    if self.__exp_settings.use_set_vds_range:
    #         for vds in self.__exp_settings.vds_range:
    #                self.non_gated_single_value_measurement(vds)
    #    else:
    #        self.non_gated_single_value_measurement(self.__exp_settings.drain_source_voltage)

    #    # foreach vds_voltage in Vds_range
    #    #  non_gated_single_value_measurement(vds)

    #def non_gated_single_value_measurement(self, drain_source_voltage):
    #    #self.set_drain_source_voltage(drain_source_voltage)
    #    self.perform_non_gated_single_measurement()
    #    #set vds_voltage
    #    # stabilize voltage
    #    # perform_single_measurement()
    #    pass

   

    #def generate_experiment_function(self):
    #    func = None
        
    #    print(self.__exp_settings.meas_gated_structure)
    #    print(self.__exp_settings.meas_characteristic_type)
    #    print(self.__exp_settings.use_transistor_selector)
       
    #    if not self.__exp_settings.meas_gated_structure:# non gated structure measurement
    #        func = self.non_gated_structure_meaurement_function
    #    elif self.__exp_settings.meas_characteristic_type == 0: #output curve
    #        func = self.output_curve_measurement_function
    #    elif self.__exp_settings.meas_characteristic_type == 1: #transfer curve
    #        func = self.transfer_curve_measurement_function
    #    else: 
    #        raise AssertionError("function was not selected properly")

    #    if self.__exp_settings.use_transistor_selector:
    #        def execution_function(self):
    #            for transistor in self.__exp_settings.transistor_list:
    #                self.switch_transistor(transistor)
    #                func(self)
    #        return execution_function

    #    return func



    #def perform_non_gated_single_measurement(self):
    #    raise NotImplementedError()
    #    #set overload_rejection
    #    #self.__dynamic_signal_analyzer.switch_overload_rejection(self.__exp_settings.overload_rejecion)
    #    #calibrate
    #    #if self.__exp_settings.calibrate_before_measurement:
    #    #    self.__dynamic_signal_analyzer.calibrate()
        
    #    #set averaging
    #    #self.__dynamic_signal_analyzer.set_average_count(self.__exp_settings.averages)

    #    #set display updates
    #    #self.__dynamic_signal_analyzer.set_display_update_rate(self.__exp_settings.display_refresh)

    #    #measure_temperature
    #    #if self.__exp_settings.need_measure_temperature:
    #    #    raise NotImplementedError()

    #    #switch Vfg to Vmain

    #    #measure Vmain
    #    #calculate Isample ,Rsample
    #    #measure spectra 
    #    #switch Vfg to Vmain
    #    #measure Vmain
    #    #calculate Isample ,Rsample
    #    #calculate resulting spectra
    #    #write data to measurement file and experiment file
    #    print("performing perform_non_gated_single_measurement")
    #    self._counter+=1
    #    print("count: {0}".format(self._counter))
    #    #pass
        
    #def __initialize_analyzer(self,analyzer):
    #    #analyzer = self.__dynamic_signal_analyzer
    #    analyzer.remove_time_capture_data()
    #    analyzer.clear_status()

    #    #set mode
    #    analyzer.select_instrument_mode(HP35670A_MODES.FFT)
    #    analyzer.switch_input(HP35670A_INPUTS.INP2, False)
    #    analyzer.select_active_traces(HP35670A_CALC.CALC1, HP35670A_TRACES.A)
    #    analyzer.select_real_format(64)
    #    analyzer.select_ascii_format()
    #    analyzer.select_power_spectrum_function(HP35670A_CALC.CALC1)
    #    analyzer.select_voltage_unit(HP35670A_CALC.CALC1)
    #    analyzer.switch_calibration(False)
    #    analyzer.set_frequency_resolution(1600)
    #    analyzer.set_source_voltage(5)
    #    #calibrate
    #    if self.__exp_settings.calibrate_before_measurement:
    #        analyzer.calibrate()
        
    #    #set averaging
    #    analyzer.switch_averaging(True)
    #    analyzer.set_average_count(self.__exp_settings.averages)
    #    analyzer.set_display_update_rate(self.__exp_settings.display_refresh)
    #    #set overload_rejection
    #    analyzer.switch_overload_rejection(self.__exp_settings.overload_rejecion)
        
        
    #    analyzer.set_frequency_start(0)
    #    analyzer.set_frequency_stop(1600)
    #    return analyzer

    #def perform_single_measurement(self):
    #    if self._simulate:
    #        for i in range(5):
    #            print("simulating experiment")
    #            rang = 0 #np.random.choice([0,1])
    #            max_counter = 10
    #            counter = 0
    #            need_exit = self.exit.is_set
                
    #            self._data_handler.open_measurement("MyMeas{0}".format(i))#.send_process_start_command()
    #            self._data_handler.start_sample_voltage = np.random.random_sample()
    #            self._data_handler.send_measurement_info()
    #            while (not need_exit()) and counter < max_counter:
    #                data = 10**-9 * np.random.random(1600)
    #                self._data_handler.update_spectrum(data,0)
    #                self._data_handler.update_spectrum(data,1)
    #                counter+=1
    #                time.sleep(0.5)
    #            self._data_handler.end_sample_voltage = np.random.random_sample()
    #            self._data_handler.send_measurement_info()
    #            self._data_handler.close_measurement()
    #            if need_exit():
    #                return
    #            #self._data_handler.send_measurement_finished_command()#send_process_end_command()
    #        return

    #    analyzer = self.__initialize_analyzer(self.__dynamic_signal_analyzer)

    #    #measure_temperature
    #    #measure Vds, Vfg
    #    #switch Vfg to Vmain
    #    #measure Vmain
    #    #calculate Isample ,Rsample
    #    #measure spectra 
    #    print(analyzer.get_points_number(HP35670A_CALC.CALC1))
    #    analyzer.init_instrument()

    #    analyzer.wait_operation_complete()
        
    #    str_data = analyzer.get_data(HP35670A_CALC.CALC1)
    #    data = np.fromstring(str_data, sep = ',')

        

    #    rang = 0
    #    self._data_handler.update_spectrum(data,rang)
    #    #measure Vds, Vfg
    #    #switch Vfg to Vmain
    #    #measure Vmain
    #    #calculate Isample ,Rsample
    #    #calculate resulting spectra
    #    #write data to measurement file and experiment file
    #    print("performing perform_single_measurement")
    #    self._counter+=1
    #    print("count: {0}".format(self._counter))
    #    #pass


    #def perform_experiment(self):
    #    function_to_execute = self.generate_experiment_function()
    #    self._data_handler.open_experiment(self.__exp_settings.experiment_name)
    #    #self._data_handler.send_process_start_command()
    #    function_to_execute()
    #    self._data_handler.close_experiment()


    #def stop(self):
    #    self.exit.set()

    #def run(self):
    #    sys.stdout = open("log.txt", "w")
    #    cfg = Configuration()
    #    self.initialize_settings(cfg)
    #    self.perform_experiment()



    #class DataHandler:  #(QtCore.QObject):
    ##spectrum_updated_signal = QtCore.pyqtSignal(int, dict) # int - range, dict - data{f:frequency, d:data}
    ##resulting_spectrum_updated_signal = QtCore.pyqtSignal(dict)
    ##timetrace_updated_signal = QtCore.pyqtSignal(object)
    ## should gether data and 
    ## 1 - save to file
    ## 2 - notify visualization
    ##meas_ranges:
    ##{0 - range number: (0 - start freq, 1600- end freq, 1 - freq step) - list of params }
    #def _get_frequencies(self, spectrum_ranges):
    #    result = {}
    #    for k,v in spectrum_ranges.items():
    #        start,stop,step = v
    #        nlines = 1+(stop-start)/step
    #        result[k] = np.linspace(start,stop, nlines, True)
    #    return result

    #def __init__(self, working_directory, measurement_type = MeasurementTypes.spectrum, spectrum_ranges = {0: (1,1600,1),1:(64,102400,64)}, parent = None, input_data_queue = None):
    #    #super().__init__(parent)
    #    #assert isinstance(measurement_type, type(MeasurementTypes))
    #    self._input_data_queue = None
    #    if input_data_queue:
    #        #assert isinstance(input_data_queue, JoinableQueue)
    #        self._input_data_queue = input_data_queue
    
    #    assert isinstance(working_directory, str)
    #    self._working_directory = working_directory

    #    self._spectrum_ranges = spectrum_ranges
    #    self._frequencies = self._get_frequencies(spectrum_ranges)
    #    self._spectrum_data = {}   

    #    self._current_measurement_info = None
    #    #assert isinstance(self._current_measurement_info,MeasurementInfo)
    #    self._counter = 0
    
    #@property
    #def start_temperature(self):
    #    return self._current_measurement_info._measured_temp_start
    
    #@start_temperature.setter
    #def start_temperature(self, value):
    #    self._current_measurement_info._measured_temp_start = value

    #@property
    #def end_temperature(self):
    #    return self._current_measurement_info._measured_temp_end
    
    #@end_temperature.setter
    #def end_temperature(self, value):
    #    self._current_measurement_info._measured_temp_end = value

    #@property
    #def start_main_voltage(self):
    #    return self._current_measurement_info._measured_main_voltage_start
    
    #@start_main_voltage.setter
    #def start_main_voltage(self, value):
    #    self._current_measurement_info._measured_main_voltage_start = value

    #@property
    #def end_main_voltage(self):
    #    return self._current_measurement_info._measured_main_voltage_end
    
    #@end_main_voltage.setter
    #def end_main_voltage(self, value):
    #    self._current_measurement_info._measured_main_voltage_end = value

    #@property
    #def start_sample_voltage(self):
    #    return self._current_measurement_info.start_sample_voltage
    
    #@start_sample_voltage.setter
    #def start_sample_voltage(self, value):
    #    self._current_measurement_info.start_sample_voltage = value

    #@property
    #def end_sample_voltage(self):
    #    return self._current_measurement_info.end_sample_voltage
    
    #@end_sample_voltage.setter
    #def end_sample_voltage(self, value):
    #    self._current_measurement_info.end_sample_voltage = value

    #def _send_command(self,command):
    #    q = self._input_data_queue
    #    if q:
    #        q.put_nowait({'c': command})

    #def _send_command_with_param(self,command,param):
    #    q = self._input_data_queue
    #    if q:
    #        q.put_nowait({'c':command, 'p':param})

    #def open_experiment(self,experiment_name):
    #    self._send_command_with_param(ExperimentCommands.EXPERIMENT_STARTED,experiment_name)    

    #def close_experiment(self):
    #    self._send_command(ExperimentCommands.EXPERIMENT_STOPPED)

    #def open_measurement(self,measurement_name):
    #    self._current_measurement_info = MeasurementInfo(measurement_name)
    #    self._send_command_with_param(ExperimentCommands.MEASUREMENT_STARTED,measurement_name) 

    #def close_measurement(self):
    #    self._send_command(ExperimentCommands.MEASUREMENT_FINISHED)

    #def send_measurement_info(self):
    #    self._send_command_with_param(ExperimentCommands.MEASUREMENT_INFO, self._current_measurement_info)

    #def update_spectrum(self, data,rang = 0):
    #    #range numeration from 0:   0 - 0 to 1600HZ
    #    #                           1 - 0 to 102,4KHZ
    #    self._spectrum_data[rang] = data
    #    q = self._input_data_queue
    #    freq = self._frequencies[rang]
    #    print(rang)
    #    print(len(freq))
    #    print(len(data))

    #    result = {'c': ExperimentCommands.DATA, 'r': rang, 'f': freq, 'd':data, 'i': self._counter}
    #    self._counter+=1
    #    if q:
    #        q.put_nowait(result) 
        
    #def update_resulting_spectrum(self):
    #    pass

    #def update_timetrace(self,data):
    #    raise NotImplementedError()

    #def reset(self):
    #    raise NotImplementedError()