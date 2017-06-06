from n_enum import enum
from CommunicationLayer import VisaInstrument

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

