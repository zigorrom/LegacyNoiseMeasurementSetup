
def generate_measurement_info_filename(measurement_name, measurement_count, file_extension = "dat"):
    return "{0}_{1}.{2}".format(measurement_name,measurement_count, file_extension)

class MeasurementInfo:
    def __init__(self, measurement_filename = "", measurement_count = 0,file_extension = "dat"):
        self._measurement_filename = measurement_filename
        self._measurement_count = measurement_count
        self._measurement_file_extension = file_extension

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
    def measurement_count(self):
        return self._measurement_count

    @measurement_count.setter
    def measurement_count(self,value):
        self._measurement_count = value

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
        return self._measured_sample_voltage_end
    
    @end_sample_voltage.setter
    def end_sample_voltage(self, value):
        self._measured_sample_voltage_end = value
        
    @property
    def start_gate_voltage(self):
        return self._measured_gate_voltage_start
    
    @start_gate_voltage.setter
    def start_gate_voltage(self,value):
        self._measured_gate_voltage_start = value

    @property
    def end_gate_voltage(self):
        return self._measured_gate_voltage_end
    
    @end_gate_voltage.setter
    def end_gate_voltage(self,value):
        self._measured_gate_voltage_end = value

    def __str__(self):
        list = [self.start_sample_voltage, 
                self._sample_current_start,
                self._equivalent_resistance_start,
                generate_measurement_info_filename(self.measurement_filename, self.measurement_count,self._measurement_file_extension),
                None,
                self.end_main_voltage,
                self.start_sample_voltage,
                self.start_main_voltage,
                self._sample_resistance_start,
                self._sample_resistance_end,
                self.start_temperature,
                self.end_temperature,
                None,
                None,
                self.end_gate_voltage
                ]
        representation = "\t".join(map(str,list)) + '\n'
        return representation
        



