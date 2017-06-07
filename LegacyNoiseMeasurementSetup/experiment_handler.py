
from nodes import ExperimentSettings, ValueRange, HardwareSettings
from configuration import Configuration
from hp34401a_multimeter import HP34401A,HP34401A_FUNCTIONS
from hp35670a_dsa import HP3567A, HP35670A_MODES,HP35670A_CALC, HP35670A_TRACES,HP35670A_INPUTS
from arduino_controller import ArduinoController
from motorized_potentiometer import MotorizedPotentiometer


class Experiment:
    def __init__(self):
        #self.__hardware_settings = None
        #self.__exp_settings = ExperimentSettings()
        #self.__initialize_hardware()

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


    def initialize_settings(self, configuration):
        assert isinstance(configuration, Configuration)
        self.__config = configuration
        self.__exp_settings = configuration.get_node_from_path("Settings.ExperimentSettings")
        assert isinstance(self.__exp_settings, ExperimentSettings)
        self.__hardware_settings = configuration.get_node_from_path("Settings.HardwareSettings")
        assert isinstance(self.__hardware_settings, HardwareSettings)
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
        pass

    def set_front_gate_voltage(self,voltage):
        print("settign front gate voltage: {0}".format(voltage))
        channel = self.__hardware_settings.gate_potentiometer_channel
        potentiometer = MotorizedPotentiometer(self.__arduino_controller, channel, self.__main_gate_multimeter)
        potentiometer.set_voltage(voltage)



    def set_drain_source_voltage(self,voltage):
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
        
        print(analyzer.get_data(HP35670A_CALC.CALC1))
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


if __name__ == "__main__":
    cfg = Configuration()
    #settings = cfg.get_node_from_path("Settings.ExperimentSettings")
    #assert isinstance(settings, ExperimentSettings)
    #print(settings)


    exp = Experiment()
    exp.initialize_settings(cfg)
    exp.perform_experiment()


    pass