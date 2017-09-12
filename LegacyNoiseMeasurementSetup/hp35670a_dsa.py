import time
from n_enum import enum
from communication_layer import VisaInstrument, instrument_await_function
import numpy as np

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

    def switch_averaging(self,state):
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

    def set_frequency_start(self, value, units = None):
        assert isinstance(value, float) or isinstance(value,int)
        request = "SENS:FREQ:STAR {0}".format(value)
        if units:
            request = "{0} {1}".format(request, units)
        self.write(request)#"SENS:FREQ:STAR {0}".format(value))

    def set_frequency_stop(self,value, units = None):
        assert isinstance(value, float) or isinstance(value, int)
        request = "SENS:FREQ:STOP {0}".format(value)
        if units:
            request = "{0} {1}".format(request, units)
        self.write(request)#"SENS:FREQ:STOP {0}".format(value))

    @instrument_await_function
    def get_data(self,calc):
        assert calc in HP35670A_CALC.indexes
        data = self.query("{}:DATA?".format(HP35670A_CALC[calc]))
        res = np.fromstring(data,sep=",")
        return res


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

    def operation_completed(self):
        self.write("*OPC")

    def operation_completed_query(self):
        self.query("*OPC?")


class VoltageMeasurementSwitch:
    def __init__(self, analyzer):
        assert isinstance(analyzer, HP3567A)
        self.analyzer = analyzer

    def switch_to_main(self):
        self.analyzer.output_state(False)

    def switch_to_sample_gate(self):
        self.analyzer.output_state(True)


if __name__=="__main__":
    
    res = "GPIB0::6::INSTR"
    dev = HP3567A(res)
    dev.abort()
    dev.calibrate()
    dev.set_source_voltage(6.6)
    dev.output_state(True)
    time.sleep(2)
    dev.output_state(False)
    print(HP35670A_MODES.FFT)
    dev.select_instrument_mode(HP35670A_MODES.FFT)
    dev.switch_input(HP35670A_INPUTS.INP2, False)
    dev.select_active_traces(HP35670A_CALC.CALC1, HP35670A_TRACES.A)
    #dev.select_real_format(64)
    dev.select_ascii_format()
    dev.select_power_spectrum_function(HP35670A_CALC.CALC1)
    dev.select_voltage_unit(HP35670A_CALC.CALC1)
    dev.switch_calibration(False)
    dev.set_average_count(50)
    dev.set_display_update_rate(1)
    dev.set_frequency_resolution(1600)
    dev.set_frequency_start(0)
    dev.set_frequency_stop(102.4,"KHZ")

    print(dev.get_points_number(HP35670A_CALC.CALC1))


    dev.init_instrument()
    dev.wait_operation_complete()

    print(dev.get_data(HP35670A_CALC.CALC1))
    pass