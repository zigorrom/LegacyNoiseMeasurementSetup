import os
import sys
import time

import numpy as np
from scipy import signal

from communication_layer import VisaInstrument, instrument_await_function



def Convertion(a):
    pol_idx = a[2]
    range_val = ai_all_fRanges[a[1]]
    f = ai_convertion_functions[pol_idx]
    # starting from 4 since the header has 4 items
    timetrace = f(range_val,a[4:])
##    fft = np.fft.fft(timetrace)
##    res = np.concatenate(timetrace,fft).reshape((timetrace.size,2))
    return timetrace

SWITCH_STATE_ON, SWITCH_STATE_OFF = SWITCH_STATES = ["ON","OFF"]
SWITCH_STATES_CONVERTER = {"0": False,
                           "1": True,
                           SWITCH_STATE_ON: True,
                           SWITCH_STATE_OFF: False}

AI_CHANNEL_101, AI_CHANNEL_102, AI_CHANNEL_103, AI_CHANNEL_104 = AI_CHANNELS = [101, 102, 103, 104]
AO_CHANNEL_201, AO_CHANNEL_202 = AO_CHANNELS = [201,202]


DIGITAL_MODE_INPUT, DIGITAL_MODE_OUTPUT = DIGITAL_MODES = ["INP", "OUTP"]
DIG_CHANNEL_501, DIG_CHANNEL_502, DIG_CHANNEL_503, DIG_CHANNEL_504 = DIG_CHANNELS = [501, 502, 503, 504]

DIG_CH501_BIT0 = (DIG_CHANNEL_501, 0)
DIG_CH501_BIT1 = (DIG_CHANNEL_501, 1)
DIG_CH501_BIT2 = (DIG_CHANNEL_501, 2)
DIG_CH501_BIT3 = (DIG_CHANNEL_501, 3)
DIG_CH501_BIT4 = (DIG_CHANNEL_501, 4)
DIG_CH501_BIT5 = (DIG_CHANNEL_501, 5)
DIG_CH501_BIT6 = (DIG_CHANNEL_501, 6)
DIG_CH501_BIT7 = (DIG_CHANNEL_501, 7)
DIG_CH502_BIT0 = (DIG_CHANNEL_502, 0)
DIG_CH502_BIT1 = (DIG_CHANNEL_502, 1)
DIG_CH502_BIT2 = (DIG_CHANNEL_502, 2)
DIG_CH502_BIT3 = (DIG_CHANNEL_502, 3)
DIG_CH502_BIT4 = (DIG_CHANNEL_502, 4)
DIG_CH502_BIT5 = (DIG_CHANNEL_502, 5)
DIG_CH502_BIT6 = (DIG_CHANNEL_502, 6)
DIG_CH502_BIT7 = (DIG_CHANNEL_502, 7)
DIG_CH501_BIT0 = (DIG_CHANNEL_503, 0)
DIG_CH501_BIT1 = (DIG_CHANNEL_503, 1)
DIG_CH501_BIT2 = (DIG_CHANNEL_503, 2)
DIG_CH501_BIT3 = (DIG_CHANNEL_503, 3)
DIG_CH501_BIT0 = (DIG_CHANNEL_504, 0)
DIG_CH501_BIT1 = (DIG_CHANNEL_504, 1)
DIG_CH501_BIT2 = (DIG_CHANNEL_504, 2)
DIG_CH501_BIT3 = (DIG_CHANNEL_504, 3)

DIGITAL_BIT_ON, DIGITAL_BIT_OFF = DIGITAL_BIT_STATES = ['1','0']

UNIPOLAR, BIPOLAR = POLARITIES = ["UNIP", "BIP"]

RANGE_125, RANGE_25, RANGE_5, RANGE_10 = DAQ_RANGES = [1.25, 2.5, 5, 10]
AUTO_RANGE = "AUTO"
AI_RANGES = [AUTO_RANGE, RANGE_125, RANGE_25, RANGE_5, RANGE_10]

MAX_INT16 = 65536
MAX_INT16_HALF = 32768

SINGLE_SHOT_READY, SINGLE_SHOT_IN_PROCESS = ["YES", "NO"]
ACQUISITION_EMPTY, ACQUISITION_FRAGMENT, ACQUSITION_DATA, ACQUISITION_OVERLOAD = ["EPTY","FRAG","DATA","OVER"]


def BipolarConversionFunction(range_value, data_code):
    return (data_code*range_value)/MAX_INT16_HALF

def UnipolarConversionFunction(range_value, data_code):
    return (data_code/MAX_INT16+0.5)*range_value

AI_CONVERSION_FUNCTION = {BIPOLAR: BipolarConversionFunction,
                          UNIPOLAR: UnipolarConversionFunction}

ERROR_SPECIFIED_CHANNEL_NOT_EXISTING = "Specified channel is not existing"



def check_channel_exists(channel):
    if channel in AI_CHANNELS:
        return True
    elif channel in AO_CHANNELS:
        return True
    elif channel in DIG_CHANNELS:
        return False

def check_analog_in_channel_exists(channel):
    if channel in AI_CHANNELS:
        return True
    else:
        return False

def check_analog_out_channel_exists(channel):
    if channel in AO_CHANNELS:
        return True
    else:
        return False

def check_analog_channel_exists(channel):
    return check_analog_in_channel_exists(channel) or check_analog_out_channel_exists(channel)

def check_dig_channel_exists(channel):
    if channel in DIG_CHANNELS:
        return True
    else:
        return False

def check_dig_bit_exists(channel, bit):
    if check_dig_channel_exists(channel):
        if bit < 0:
            return False
        elif channel == DIG_CHANNEL_501 or channel == DIG_CHANNEL_502:
            if bit<8:
                return True
        elif channel == DIG_CHANNEL_503 or channel == DIG_CHANNEL_504:
            if bit<4:
                return True
    else:
        return False

def assert_state(state):
    assert state in SWITCH_STATES, "Wrong state!"
    return True

def assert_dig_mode(mode):
    assert mode in DIGITAL_MODES, "Wrong mode!"
    return True

def assert_polarity(polarity):
    assert polarity in POLARITIES, "Wrong polarity!"
    return True

def assert_range(range_value):
    assert range_value in DAQ_RANGES, "Wrong range!"
    return True

def assert_analog_range(range_value):
    assert range_value in AI_RANGES, "Wrong range!"
    return True

def check_single_shot_data_is_ready(state):
    if state == SINGLE_SHOT_READY:
        return True

def check_continuous_acquisition_data_is_ready(state):
    if state == ACQUISITION_OVERLOAD:
        raise OverflowError("Buffer is overloaded")
    elif state == ACQUSITION_DATA:
        return True
    else:
        return False


class AgilentU2542A_DSP(VisaInstrument):
    def __init__(self, resource):
        super().__init__(resource)


    def initialize_instrument(self, resource):
        pass

    def set_sample_rate(self,sample_rate):
        if sample_rate < 3 or sample_rate > 500000:
            raise Exception("Sample rate is out of allowed range")
        self.write("ACQ:SRAT {0}".format(sample_rate))


    def set_single_shot_acquisition_points(self, points):
        self.write("ACQ:POIN {0}".format(points))

    def set_continuous_acquisition_points(self,points):
        self.write("WAV:POIN {0}".format(points))


    def ask_idn(self):
        return self.query("*IDN?")
     
            
    def clear_status(self):
        self.write("*CLS")

    def reset_device(self):
        self.write("*RST")


    def switch_enabled(self, channel, state):
        assert check_analog_channel_exists(channel), "Channel is not existing in analog channels"
        assert_state(state)
        self.write("ROUT:ENAB {0},(@{1})".format(state,channel))
        

    def switch_enabled_for_channels(self, channels, state):
        assert all((check_analog_channel_exists(channel) for channel in channels)), "At least one of channels is not existing"
        assert_state(state)
        self.write("ROUT:ENAB {0},(@{1})".format(state, ",".join(channels)))

    def check_channels_enabled(self, channels):
        if isinstance(channels, int):
            channels = [channels]

        assert all((check_analog_channel_exists(channel) for channel in channels)), "At least one of channels is not existing"
        result = self.query("ROUT:ENAB? (@{0})".format(",".join(channels)))
        spl = result.split(',')
        assert len(spl) == len(channels), "Inconsistent result"
        return {channel: SWITCH_STATES_CONVERTER[state] for (channel, state) in zip(channels, spl) }


    def set_digital_mode(self, channel, mode):
        assert check_dig_channel_exists(channel), "Digital channel is not existing"
        assert_dig_mode(mode)
        self.write("CONF:DIG:DIR {0},(@{1})".format(mode,channel))

    def set_digital_mode_for_channels(self, channels, mode):
        assert all((check_dig_channel_exists(channel) for channel in channels)),  "At least one of channels is not existing"
        assert_dig_mode(mode)
        self.write("CONF:DIG:DIR {0},(@{1})".format(mode,",".join(channels)))

    def set_polarity(self, channel, polarity):
        assert check_analog_channel_exists(channel)
        assert_polarity(polarity)
        self.write("ROUT:CHAN:POL {0}, (@{1})".format(polarity, channel))

    def set_polarity_for_channels(self, channels, polarity):
        assert all((check_analog_channel_exists(channel) for channel in channels )), "At least one of channels is not existing"
        assert_polarity(polarity)
        self.write("ROUT:CHAN:POL {0}, (@{1})".format(polarity, ",".join(channels)))

    def set_range(self, channel, range_value):
        assert check_analog_in_channel_exists(channel), "Specified analog in channel is not existing"
        assert_range(range_value)
        self.write("ROUT:RANG {0}, (@{1})".format(range_value,channel))

    def set_range_for_channels(self, channels, range_value):
        assert all((check_analog_in_channel_exists(channel) for channel in channels)), "At least one of channels is not existing"
        assert_range(range_value)
        self.write("ROUT:RANG {0}, (@{1})".format(range_value, ",".join(channels)))

    def digital_write(self, channel, value):
        assert check_dig_channel_exists(channel), "Specified channel is not existing"
        self.write("SOUR:DIG:DATA {0},(@{1})".format(value,channel))

    def digital_write_channels(self, channels, value):
        assert all((check_dig_channel_exists(channel) for channel in channels)), "At least one of channels is not existing"
        self.write("SOUR:DIG:DATA {0},(@{1})".format(value,",".join(channels)))

    def digital_write_bit(self,dig_bit, value):
        assert isinstance(dig_bit, tuple)
        channel, bit = dig_bit
        assert check_dig_bit_exists(channel, bit), "Specified digital bit is not exisiting"
        self.write("SOUR:DIG:DATA:BIT {0}, {1}, (@{2})".format(value,bit,channel))

    def digital_pulse_bit(self, dig_bit, pulse_width = 0.005):
        assert isinstance(dig_bit, tuple)
        channel, bit = dig_bit
        assert check_dig_bit_exists(channel, bit), "Specified digital bit is not exisiting"
        str_format = "SOUR:DIG:DATA:BIT {0}, {1}, (@{2})"
        self.write(str_format.format(DIGITAL_BIT_OFF,bit,channel))
        time.sleep(pulse_width)
        self.write(str_format.format(DIGITAL_BIT_ON,bit,channel))
        time.sleep(pulse_width)
        self.write(str_format.format(DIGITAL_BIT_OFF,bit,channel))

    def digital_read_bit(self, dig_bit):
        assert isinstance(dig_bit, tuple)
        channel, bit = dig_bit
        assert check_dig_bit_exists(channel, bit), "Specified digital bit is not exisiting"
        value = self.query("SOUR:DIG:DATA:BIT? {1}, (@{2})".format(value,bit,channel))
        return int(value)

    def digital_read(self,channel):
        assert check_dig_channel_exists(channel), "Specified channel is not existing"
        value = self.query("SOUR:DIG:DATA? (@{0})".format(channel))
        return int(value)

    def digital_measure(self, channel):
        raise NotImplementedError()


    def digital_measure_channels(self, channels):
        raise NotImplementedError()

    
    def analog_set_range(self, channel, range_value):
        assert check_analog_in_channel_exists(channel)
        assert_analog_range(range_value)
        self.write("VOLT:RANG {0}, (@{1})".format(range_value, channel))

    def analog_set_range_for_channels(self, channels, range_value):
        assert all((check_analog_in_channel_exists(channel) for channel in channels )), "At least one of channels is not existing"
        assert_analog_range(range_value)
        self.write("VOLT:RANG {0}, (@{1})".format(range_value, ",".join(channels)))

    def analog_set_polarity(self, channel, polarity):
        assert check_analog_in_channel_exists(channel)
        assert_polarity(polarity)
        self.write("VOLT:POL {0}, (@{1})".format(polarity, channel))

    def analog_set_polarity_for_channels(self, channels, polarity):
        assert all((check_analog_in_channel_exists(channel) for channel in channels )), "At least one of channels is not existing"
        assert_polarity(polarity)
        self.write("VOLT:POL {0}, (@{1})".format(polarity, ",".join(channels)))

    def analog_set_averaging(self, averaging):
        assert averaging > 0 and averaging < 1001, "Averaging is out of range"
        self.write("VOLT:AVER {0}".format(aver))

    def analog_averaging_query(self):
        value = self.query("VOLT:AVER?")
        return int(value)

    def analog_measure(self, channel):
        assert check_analog_in_channel_exists(channel)
        value = self.query("MEAS? (@{0})".format(channel))
        return float(value)

    def analog_measure_channels(self, channels):
        assert all((check_analog_in_channel_exists(channel) for channel in channels)), "At least one of channels is not existing"
        str_result = self.query("MEAS? (@{0})".format(",".join(channels)))
        spl = result.split(',')
        assert len(spl) == len(channels), "Inconsistent result"
        return {channel: float(value) for (channel, value) in zip(channels, spl)}

    def analog_set_source_polarity(self, channel, polarity):
        assert check_analog_out_channel_exists(channel)
        assert_polarity(polarity)
        self.write("SOUR:VOLT:POL {0}, (@{1})".format(polarity, channel))

    def analog_set_source_polarity_for_channels(self,channels, polarity):
        assert(all(check_analog_out_channel_exists(channel) for channel in channels))
        assert_polarity(polarity)
        self.write("SOUR:VOLT:POL {0}, (@{1})".format(polarity, ",".join(channels)))

    def analog_source_voltage(self, channel, voltage):
        assert check_analog_out_channel_exists(channel)
        assert voltage >= -10 and voltage <= 10
        self.write("SOUR:VOLT {0}, (@{1})".format(voltage, channel))

    def analog_source_voltage_for_channels(self, channels, voltage):
        assert all((check_analog_out_channel_exists(channel) for channel in channels))
        assert voltage >= -10 and voltage <= 10
        self.write("SOUR:VOLT {0}, (@{1})".format(voltage, ",".join(channels)))

    def analog_set_output_state(self,state):
        assert state in SWITCH_STATES
        self.write("OUTP {0}".format(state))

    def start_acquisition(self):
        self.write("RUN")

    def start_single_shot_acquisition(self):
        self.write("DIG")

    def stop_acquisition(self):
        self.write("STOP")

    def single_shot_acquisition_completed(self):
        return self.query("WAV:COMP?")

    def continuous_acquisition_state(self):
        return self.query("WAV:STAT?")

    def acquisition_read_raw_data(self):
        self.write("WAV:DATA?")
        #return self





def test():
    pass



def main():
        d = AgilentU2542A('ADC')
##        plt.ion()
        try:
            
            counter = 0
            d.daq_reset()
            d.daq_setup(500000,50000)
            d.daq_set_enable_ai_channels(STATES.ON,[AI_CHANNELS.AI_101,AI_CHANNELS.AI_102,AI_CHANNELS.AI_103,AI_CHANNELS.AI_104])
            d.daq_run()
            print("started")
            init_time = time.time()
            max_count = 10000
            while counter < max_count:
                try:
                    if d.daq_is_data_ready():

                        counter += 1
                        t = time.time()-init_time

                        data = d.daq_read_data()
##                        q.put(t)
##                        q.put(data)
##                        if counter % 10 == 0:
##                            plt.plot(data[0])
##                            plt.pause(0.05)
##                        print()
                        print(t)
                        print(len(data))
                        print(data)
                        
                        

                except Exception as e:
                    err = str(e)
                    print(err)
                    if err== 'overload':
                        counter = max_count
                
                    
        except Exception as e:
##            pass
            print ("exception"+str(e))
        finally:
            d.daq_stop()
            d.daq_reset()
            print("finished")


if __name__ == "__main__":

    
    os.system("pause")

   
