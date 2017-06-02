import visa
import time
import serial
from n_enum import enum

def instrument_await_function(func):
        def wrapper(self,*args,**kwargs):
            prev_timeout = self.instrument.timeout
            self.instrument.timeout = None
            result = func(self,*args,**kwargs)
            self.instrument.timeout = prev_timeout 
            return result
        return wrapper


class SerialInstrument:
    def __init__(self, resource, baud_rate = 9600):
        self.__port = serial.Serial(
            port = resource, 
            baudrate = baud_rate
            )
        self.__termination_char = "\n"
        self.__port.flushInput()
        self.__port.flushOutput()

    @property
    def termination_char(self):
        return self.__termination_char
    
    @termination_char.setter
    def termination_char(self,value):
        self.__termination_char = value

    def open(self):
        if not self.isOpen():
            self.__port.open()

    def close(self):
        self.__port.close()

    def isOpen(self):
        return self.__port.isOpen()

    def write(self, string):
        assert self.isOpen()
        print("sending to device: {0}".format(string))
        self.__port.write(string)

    def read(self, num_of_bytes = 1):
        assert self.isOpen()
        return self.__port.read(num_of_bytes).decode()

    def read_until_termination(self):
        assert self.isOpen()
        read_chars = []
        current_char = None
        while current_char != self.termination_char:
            current_char = self.read()
            read_chars.append(current_char)

        return "".join(read_chars)

    def query(self,string):
        assert self.isOpen()
        self.write(string)
        return self.read_until_termination()




ARDUINO_FUNCTIONS = enum("Watchdog","Acknowledge","SwitchChannel", "Error", "MotorCommand")

class ArduinoController(SerialInstrument):
    def __init__(self, resource, baud_rate = 9600):
        super().__init__(resource, baud_rate)
        self.termination_char = ';'
        
    def read_idn(self):
        return self.query("{0};".format(ARDUINO_FUNCTIONS.Watchdog).encode())

    def switch_channel(self, channel, state):
        self.write('{0},{1},{2};'.format(ARDUINO_FUNCTIONS.SwitchChannel,channel, 1 if state else 0).encode())
        self._parse_response(self.read_until_termination())
    
    def set_motor_speed(self, channel, speed):
        pass

    def _parse_response(self,response):
        print(response) 
    
        





class VisaInstrument:
    def __init__(self, resource):
        rm = visa.ResourceManager()
        self.__instrument = rm.open_resource(resource, write_termination = '\n',read_termination='\n')

    def write(self,string):
        assert isinstance(string, str)
        print("writing to device: {0}".format(string))
        self.__instrument.write(string)

    def query(self,string):
        assert isinstance(string, str)
        print("querying from device: {0}".format(string))
        return self.__instrument.ask(string)

    def read(self):
        return self.__instrument.read()


HP34401A_FUNCTIONS = enum("AVER")

class HP34401A(VisaInstrument):
    def __init__(self, resource):
        super().__init__(resource)

    def reset(self):
        self.write("*RST")

    def clear_status(self):
        self.write("*CLS")

    def query_operation_completed(self):
        return self.query("*OPC?")

    def set_nplc(self,nplc):
        assert isinstance(nplc, float)or isinstance(nplc, int)
        assert nplc > 0, "nplc should be greater than 0"
        self.write("VOLT:DC:NPLC {0}".format(nplc))

    def set_trigger_count(self,count):
        assert  isinstance(count, int)
        self.write("TRIG:COUN {0}".format(count))

    def switch_beeper(self,state):
        self.write("SYST:BEEP:STAT {0}".format("ON" if state else "OFF"))

    def switch_high_ohmic_mode(self,state):
        self.write("INP:IMP:AUTO {0}".format("ON" if state else "OFF"))

    def set_function(self,func):
        assert func in HP34401A_FUNCTIONS.indexes
        self.write("CALC:FUNC {0}".format(HP34401A_FUNCTIONS[func]))

    def switch_stat(self,state):
        self.write("CALC:STAT {0}".format("ON" if state else "OFF"))

    def switch_autorange(self,state):
        self.write("SENS:VOLT:DC:RANG:AUTO {0}".format("ON" if state else "OFF"))

    def init_instrument(self):
        self.write("INIT")

    @instrument_await_function
    def read_voltage(self):
        return float(self.query("MEAS:VOLTAGE:DC?")) #"CALC:AVER:AVER?"))

    @instrument_await_function
    def read_average(self):
        return float(self.query("CALC:AVER:AVER?"))


HP35670A_MODES = enum("FFT", "OCT", "ORD", "SINE", "HIST", "CORR")
HP35670A_INPUTS = enum("INP1","INP2")
HP35670A_CALC = enum("CALC1","CALC2","CALC3","CALC4")
HP35670A_TRACES = enum("A","B","C","D")

class HP3567A(VisaInstrument):
    def __init__(self, resource):
        super().__init__(resource)
   
    def initialize_instrument(self):
        raise NotImplementedError()

    def output_state(self, state):
        self.write("OUTPUT:STAT {0}".format("ON" if state else "OFF"))

    def set_source_voltage(self,voltage):
        assert isinstance(voltage, float) or isinstance(voltage, int), "Houston, we`ve got a problem"
        self.write("SOUR:VOLTAGE:OFFS {0}".format(voltage))

    def remove_time_capture_data(self):
        self.write(":TCAP:DEL")

    def select_instrument_mode(self,mode):
        """ mode can be FFT|OCTave|ORDer|SINE|HISTogram|CORRelation"""
        assert mode in HP35670A_MODES.indexes
        #print(HP35670A_MODES[mode])
        self.write("INST:SEL {0}".format(HP35670A_MODES[mode]))

    def switch_input(self,input,state):
        assert input in HP35670A_INPUTS.indexes
        self.write(":{0} {1}".format(HP35670A_INPUTS[input], "ON" if state else "OFF"))

    def select_active_traces(self, calc, trace):
        assert calc in HP35670A_CALC.indexes
        assert trace in HP35670A_TRACES.indexes
        self.write(":{0}:ACTIVE {1}".format(HP35670A_CALC[calc],HP35670A_TRACES[trace]))

    def select_real_format(self, bit_number):
        assert bit_number is 32 or bit_number is 64
        self.write("FORM:DATA REAL, {0}".format(bit_number))

    def select_ascii_format(self):
        self.write("FORM:DATA ASC, 12")

    def select_power_spectrum_function(self,calc):
        assert calc in HP35670A_CALC.indexes
        self.write("{0}:FEED '{1}'".format(HP35670A_CALC[calc], "XFR:POW {0}".format(calc+1)))

    def select_voltage_unit(self,calc):
        assert calc in HP35670A_CALC.indexes
        self.write("{0}:UNIT:VOLT 'V2/Hz'".format(HP35670A_CALC[calc]))

    def switch_calibration(self,state):
        self.write("CAL:AUTO {0}".format("ON" if state else "OFF"))

    def set_frequency_resolution(self,value):
        assert isinstance(value,int)
        self.write("FREQ:RES {0}".format(value))

    def set_averaging(self,state):
        self.write(":AVER {0}".format("ON" if state else "OFF"))

    def set_display_update_rate(self, rate):
        assert isinstance(rate,int) and rate > 0
        self.write("SENS:AVERAGE:IRES:RATE {0}".format(rate))

    def set_average_count(self,count):
        assert isinstance(count,int) and count > 0
        self.write("SENS:AVERAGE:COUNT {0}".format(count))

    def switch_overload_rejection(self,state):
        self.write("SENS:REJ:STAT {0}".format("ON" if state else "OFF"))

    def get_points_number(self,calc):
        assert calc in HP35670A_CALC.indexes
        return self.query("{0}:DATA:HEAD:POIN?".format(HP35670A_CALC[calc]))

    def set_frequency_start(self, value):
        assert isinstance(value, float) or isinstance(value,int)
        self.write("SENS:FREQ:STAR {0}".format(value))

    def set_frequency_stop(self,value):
        assert isinstance(value, float) or isinstance(value, int)
        self.write("SENS:FREQ:STOP {0}".format(value))

    @instrument_await_function
    def get_data(self,calc):
        assert calc in HP35670A_CALC.indexes
        return self.query("{}:DATA?".format(HP35670A_CALC[calc]) )


    def abort(self):
        self.write("ABORT");

    def init_instrument(self):
        self.write(":INIT");

    def clear_status(self):
        self.write("*CLS")

    @instrument_await_function
    def calibrate(self):
        return self.query("*CAL?")
     
    @instrument_await_function
    def wait_operation_complete(self):
        self.write("*WAI")


 
if __name__== "__main__":

    ard = ArduinoController("COM8", 115200)
    #ard.open();
    var = ard.read_idn()
    #print(var)
    for i in range(1,33,1):
        ard.switch_channel(i,True)

    ard.close()
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
