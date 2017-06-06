
from nodes import ExperimentSettings
from configuration import Configuration

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

    def initialize_settings(self, settings):
        assert isinstance(settings, ExperimentSettings)
        self.__exp_settings = settings


    def initialize_hardware(self):
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


if __name__ == "__main__":
    cfg = Configuration()
    settings = cfg.get_node_from_path("Settings.ExperimentSettings")
    assert isinstance(settings, ExperimentSettings)
    print(settings)


    exp = Experiment()
    exp.initialize_settings(settings)
    exp.perform_experiment()


    print(type(settings))
    print(settings.working_directory)
    pass