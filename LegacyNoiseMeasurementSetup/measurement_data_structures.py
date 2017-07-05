
class MeasurementInfo:
    def __init__(self, measurement_filename = ""):
        self._measurement_filename = measurement_filename

        self._measured_temp_start = 0
        self._measured_temp_end = 0

        self._measured_main_voltage_start = 0
        self._measured_main_voltage_end = 0

        self._measured_sample_voltage_start = 0
        self._measured_sample_voltage_end = 0
        
        self._measured_gate_voltage_start = 0
        self._measured_gate_voltage_end = 0

        self._sample_current_start = 0
        self._sample_current_end = 0

        self._sample_resistance_start = 0
        self._sample_resistance_end = 0

        self._equivalent_resistance_start = 0
        self._equivalent_resistance_end = 0

    @property
    def measurement_filename(self):
        return self._measurement_filename

    @measurement_filename.setter
    def measurement_filename(self,filename):
        self._measurement_filename = filename

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
        
    @property
    def start_gate_voltage(self):
        return self._measured_gate_voltage_start
    
    @start_gate_voltage.setter
    def start_gate_voltage(self,value):
        self._measured_gate_voltage_start = value

    @property
    def end_gate_voltage(self):
        return self._measured_gate_voltage_start
    
    @end_gate_voltage.setter
    def end_gate_voltage(self,value):
        self._measured_gate_voltage_end = value



