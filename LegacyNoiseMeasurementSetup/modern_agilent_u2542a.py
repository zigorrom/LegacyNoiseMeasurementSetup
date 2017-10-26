
import numpy as np
#install all necessary files from here http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
from scipy import signal
import time
import os
import sys
from communication_layer import VisaInstrument, instrument_await_function


maxInt16 = 65536
maxInt16div2 = 32768
def BipolarConversionFunction(range_value, data_code):
    return (data_code*range_value)/maxInt16div2

def UnipolarConversionFunction(range_value, data_code):
    return (data_code/maxInt16+0.5)*range_value
### maybe optimization of execution speed
### IMPORTANT ORDER OF FUNCTIONS IN LIST -> CORRESPONDS TO ORDER IN AI_ALL_POLARITIES
ai_convertion_functions = [BipolarConversionFunction,UnipolarConversionFunction]
##ai_vect_convertion_functions = [np.vectorize(BipolarConversionFunction, otypes = [np.float]),np.vectorize(UnipolarConversionFunction, otypes = [np.float])]

def Convertion(a):
    pol_idx = a[2]
    range_val = ai_all_fRanges[a[1]]
    f = ai_convertion_functions[pol_idx]
    # starting from 4 since the header has 4 items
    timetrace = f(range_val,a[4:])
##    fft = np.fft.fft(timetrace)
##    res = np.concatenate(timetrace,fft).reshape((timetrace.size,2))
    return timetrace





#All cahnnel names are integers


SWITCH_STATE_ON, SWITCH_STATE_OFF = SWITCH_STATES = ["ON","OFF"]
SWITCH_STATES_CONVERTER = {"0": False,
                           "1": True,
                           SWITCH_STATE_ON: True,
                           SWITCH_STATE_OFF: False}

AI_CHANNEL_101, AI_CHANNEL_102, AI_CHANNEL_103, AI_CHANNEL_104 = AI_CHANNELS = [101, 102, 103, 104]
AO_CHANNEL_201, AO_CHANNEL_202 = AO_CHANNELS = [201,202]


DIGITAL_MODE_INPUT, DIGITAL_MODE_OUTPUT = DIGITAL_MODES = ["INP", "OUTP"]
DIG_CHANNEL_501, DIG_CHANNEL_502, DIG_CHANNEL_503, DIG_CHANNEL_504 = DIG_CHANNELS = [501, 502, 503, 504]

UNIPOLAR, BIPOLAR = POLARITIES = ["UNIP", "BIP"]

RANGE_125, RANGE_25, RANGE_5, RANGE_10 = DAQ_RANGES = [1.25, 2.5, 5, 10]


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

def assert_range(range):
    assert range in DAQ_RANGES, "Wrong range!"
    return True

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

    def set_range(self, channel, range):
        assert check_analog_in_channel_exists(channel), "Specified analog in channel is not existing"
        assert_range(range)
        self.write("ROUT:RANG {0}, (@{1})".format(range,channel))

    def set_range_for_channels(self, channels, range):
        assert all((check_analog_in_channel_exists(channel) for channel in channels)), "At least one of channels is not existing"
        assert_range(range)
        self.write("ROUT:RANG {0}, (@{1})".format(range, ",".join(channels)))

    def initialize_acquisition(self):












class AgilentU2542A:
    def __init__(self,resource):
        rm = visa.ResourceManager()
        self.instrument = rm.open_resource(resource, write_termination='\n', read_termination = '\n') #write termination
        self.conversion_header = None
        self.daq_channels = []
##        print(self.daq_idn())

    def daq_idn(self):
        return self.instrument.ask("*IDN?")

##
##      ADC acquisition REGION
##

    ## SET POINTS PER SHOT
    ## SET SAMPLE RATE
    ## srate of type int
    ## points of type int
    def daq_setup(self, srate,points):
        self.instrument.write("ACQ:SRAT {0}".format(srate))
        self.instrument.write("ACQ:POIN {0}".format(points))
        self.instrument.write("WAV:POIN {0}".format(points))

    ##RESET DEVICE
    def daq_reset(self):
        self.instrument.write("*RST")
        self.instrument.write("*CLS")

    ##ENABLE CHANNELS
    ## state: type STATES
    ## channel_names: list of strings corresponding to real names of channels
    def daq_set_enable_channels(self, state, channel_names):
        ## check if channel names exist
        ## check state
        self.instrument.write("ROUT:ENAB {0},(@{1})".format(STATES[state], ",".join(channel_names)))

    ## ENABLE ANALOG IN CHANNELS
    ##  state: type STATES
    ##  channels: list of channels from AI_CHANNELS
    def daq_set_enable_ai_channels(self,state,channels):
        ## check if channels are in the range of channels
        channel_list = [AI_CHANNELS[i] for i in channels]
        self.daq_set_enable_channels(state, channel_list)
        ## self.instrument.write("ROUT:ENAB OFF,(@101:104)")
        ## self.instrument.write("ROUT:ENAB ON,(@{0})".format( ",".join(channel_list)))
        ## self.daq_init_channels()

    def daq_set_enable_ai_channel(self,state,channel):
        ai_channel = [AI_CHANNELS[channel]]
        self.daq_set_enable_channels(state,ai_channel)

    ## ENABLE ANALOG IN CHANNELS
    ##  state: type STATES
    ##  channels: list of channels from AO_CHANNELS
    def daq_set_enable_ao_channels(self,state,channels):
        channel_list = [AO_CHANNELS[i] for i in AO_CHANNELS.indexes]
        self.daq_set_enable_channels(state, channel_list)

    def daq_set_enable_ao_channel(self,state,channel):
        ao_channel = [AO_CHANNELS[channel]]
        self.daq_set_enable_channels(state, ao_channel)       
        
    ##SET POLARITY FOR CHANNELS
    ## polarity: type POLARITIES
    ## channels: type list of channels from AI_CHANNELS
    def daq_set_ai_polarity(self,polarity, channels):
        channel_list = [AI_CHANNELS[i] for i in channels]
        self.instrument.write("ROUT:CHAN:POL {0}, (@{1})".format(POLARITIES[polarity],",".join(channel_list)))

    def daq_set_ai_channel_polarity(self, polarity, channel):
        self.daq_set_ai_polarity(polarity,[channel])

    def daq_set_ao_polarity(self,polarity, channels):
        channel_list = [AO_CHANNELS[i] for i in channels]
        self.instrument.write("ROUT:CHAN:POL {0}, (@{1})".format(POLARITIES[polarity],",".join(channel_list)))

    def daq_set_ao_channel_polarity(self, polarity, channel):
        self.daq_set_ai_polarity(polarity,[channel])
    
    def daq_set_channel_polarity(self,polarity,channel):
        self.instrument.write("ROUT:CHAN:POL {0}, (@{1})".format(POLARITIES[polarity],channel))
    
    ##SET RANGE FOR CHANNELS
    ## range: type DAQ_RANGES
    ## channels: type list of channels from AI_CHANNELS
    def daq_set_range(self,rang,channels):
        channel_list = [AI_CHANNELS[i] for i in channels]
        rng = DAQ_RANGES[rang]
        self.instrument.write("ROUT:RANG {0}, (@{1})".format(rng,",".join(channel_list)))

    def daq_set_channel_range(self,rang, channel):
        rng = DAQ_RANGES[rang]
        self.instrument.write("ROUT:RANG {0}, (@{1})".format(rng,AI_CHANNELS[channel]))
        
    ##READ PARAMETERS FROM DEVICE AND INITIALIZE SOFTWARE CHANNELS
    ## reads range, polarity, and enable from device
    def daq_init_channels(self):
        
        channels = "(@101:104)" 
        range_response = self.instrument.ask("ROUT:CHAN:RANG? {0}".format(channels))
        polarity_response = self.instrument.ask("ROUT:CHAN:POL? {0}".format(channels))
        enabled_response = self.instrument.ask("ROUT:ENAB? {0}".format(channels))
        channel_range = [DAQ_RANGES.values.index(rng) for rng in range_response.split(',')]
        channel_polarity = [POLARITIES.values.index(pol) for pol in polarity_response.split(',') ]
        channel_enabled = [en for en in enabled_response.split(',')]
        self.daq_channels = [AI_Channel(ch_name = i, ch_enabled=channel_enabled[i],ch_range = channel_range[i],ch_polarity = channel_polarity[i]) for i in AI_CHANNELS.indexes]
        self.enabled_ai_channels = self.daq_get_enabled_channels()
        n_enabled_ch = len(self.enabled_ai_channels)
        arr = np.arange(n_enabled_ch).reshape((n_enabled_ch,1))
        self.conversion_header = np.hstack((arr,np.asarray([ch.ai_get_valsIdx() for ch in self.enabled_ai_channels])))
        print( self.conversion_header )
        
    ##GET ENABLED CHANNELS
    ## returns the list of enabled channels
    def daq_get_enabled_channels(self):### list( myBigList[i] for i in [87, 342, 217, 998, 500] )
        return [ch for ch in self.daq_channels if ch.ai_is_enabled()]

    ##RUN ACQUISITION
    ## starts the acquisition process
    def daq_run(self):
##        self.daq_init_channels()
        self.instrument.write("RUN")

    ##STOP ACQUISITION
    ## stops the acquisition process
    def daq_stop(self):
        self.instrument.write("STOP")
        
    ##GET ACQUISITION STATUS
    ## gets status of acquisition
    def daq_get_status(self):
        return self.instrument.ask("WAV:STAT?")
    
    ##CHECK IF DATA IS READY
    ## check if data ready to read
    ## if overloaded throws overload exception
    def daq_is_data_ready(self):
        r = self.instrument.ask("WAV:STAT?")
        if r== "DATA":
            return True
        elif r == "OVER":
            raise Exception('overload')
        return False
    
    ##READ RAW DATA
    ## return raw data
    def daq_read_raw(self):
        self.instrument.write("WAV:DATA?")
        return self.instrument.read_raw()

    ##READ DATA AS FLOAT
    ## returns array of converted data by channels
    def daq_read_data(self):
        self.instrument.write("WAV:DATA?")
        raw_data = self.instrument.read_raw()
        len_from_header = int(raw_data[2:10])
        data = raw_data[10:]
        enabled_channels = self.enabled_ai_channels
        nchan = len(enabled_channels)
        print("nchan {0}".format(nchan))
        narr = np.fromstring(data, dtype = '<i2')
        print(len(narr))
        single_channel_data_len = int(narr.size/nchan)
        narr = np.hstack((self.conversion_header, narr.reshape((single_channel_data_len,nchan)).transpose()))
        print(len(narr))
        res = np.apply_along_axis(Convertion,1,narr)
##        res_fft = np.apply_along_axis(signal.periodogram,1,narr,fs = 500000)
        return res

    ## single shot acquisition
    def daq_single_shot_read_data(self):
        self.instrument.write("DIG")
        while self.instrument.ask("WAV:COMP?")=="NO":
            continue
        return self.daq_read_data()
        
        
##
##  END ADC acquisition REGION
##

##
##  SET - MEASURE REGION
##    
    
    def dig_set_direction(self,direction,channels):
        channel_list = [DIGITAL_CHANNELS[i] for i in channels]
        self.instrument.write("CONF:DIG:DIR {0},(@{1})".format(DIGITAL_DIRECTIONS[direction], ",".join(channel_list)))

    def dig_write_channels(self,data,channels):
        channel_list = [DIGITAL_CHANNELS[i] for i in channels]
        self.instrument.write("SOUR:DIG:DATA {0},(@{1})".format(data,",".join(channel_list)))

    def dig_write_channel(self,data,channel):
##        print(data)
##        print(channel)
        self.instrument.write("SOUR:DIG:DATA {0},(@{1})".format(data,DIGITAL_CHANNELS[channel]))
                              
    def dig_write_bit_channels(self,value,bit,channels):
        channel_list = [DIGITAL_CHANNELS[i] for i in channels]
        msg =  "SOUR:DIG:DATA:BIT {0}, {1}, (@{2})".format(value,bit,",".join(channel_list))
        print(msg)
        self.instrument.write(msg)
        
    def dig_write_bit_channel(self,value,bit,channel):
        msg =  "SOUR:DIG:DATA:BIT {0}, {1}, (@{2})".format(value,bit,DIGITAL_CHANNELS[channel])
##        print("writing value {0} to bit{1}".format(value,bit))
        self.instrument.write(msg)


    def dig_measure(self,channels):
        channel_list = [DIGITAL_CHANNELS[i] for i in channels]
        vals = self.instrument.ask("MEAS:DIG? (@{0})".format(",".join(channel_list))).split(',')
        if len(vals) != len(channel_list):
            raise Exception("non equal lengths")
        res = {ch: vals[ch] for ch in channel_list}
        return res

    def dig_bit_measure(self,bit,channels):
        channel_list = [DIGITAL_CHANNELS[i] for i in channels]
        vals = self.instrument.ask("MEAS:DIG:BIT? {0}, (@{1})".format(bit,",".join(channel_list))).split(',')
        if len(vals) != len(channels):
            raise Exception("non equal lengths")
        res = {ch: vals[ch] for ch in channel_list}
        return res

    def pulse_digital_bit(self,bit,channel,pulse_width=0.005):
        self.dig_write_bit_channel(1,bit,channel)
        time.sleep(pulse_width)
        self.dig_write_bit_channel(0,bit,channel)
    
    
    
    def adc_set_voltage_range(self,rang,channels):
        channel_list = [AI_CHANNELS[i] for i in channels]
        self.instrument.write("VOLT:RANG {0}, (@{1})".format(DAQ_RANGES[rang],",".join(channel_list)))

    def adc_set_voltage_polarity(self,pol,channels):
        channel_list = [AI_CHANNELS[i] for i in channels]
        self.instrument.write("VOLT:POL {0}, (@{1})".format(POLARITIES[pol],",".join(channel_list)))

    def adc_set_voltage_average(self,aver):
        self.instrument.write("VOLT:AVER {0}".format(aver))
    
    def adc_measure(self,channels):  
        channel_list = [AI_CHANNELS[i] for i in channels]
        vals = self.instrument.ask("MEAS? (@{0})".format(",".join(channel_list))).split(',')
        if len(vals) != len(channel_list):
            raise Exception("non equal lengths")

        values_iterable = (float(val) for val in vals)
##        res = { ch: val for ch in channels for val in vals }
        res = dict(zip(channels,values_iterable))
        #res = {ch: vals[ch] for ch in channel_list}
        return res

    

    
    def dac_set_output(self, state):
        self.instrument.write("OUTPUT {0}".format(STATES[state]))
    
    def dac_source_voltage(self, value, channels):
##        self.dac_set_output(STATES.OFF)
        channel_list = [AO_CHANNELS[i] for i in channels]
        self.instrument.write("SOUR:VOLT {0}, (@{1})".format(value,",".join(channel_list)))

    def dac_source_channel_voltage(self,value,channel):
        #print("ao channel {0}".format(AO_CHANNELS[channel]))
        self.instrument.write("SOUR:VOLT {0}, (@{1})".format(value,AO_CHANNELS[channel]))

    def dac_set_polarity(self,polarity,channels):
        channel_list = [AO_CHANNELS[i] for i in channels]
        self.instrument.write("SOUR:VOLT:POL {0}, (@{1})".format(POLARITIES[polarity],",".join(channel_list)))

##
##  END SET - MEASURE REGION
##
    

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

def proc(q):
    pass

if __name__ == "__main__":


##
##
##
##          USE PIPES!!!
##
##
##

##    q = Queue()
##    p = Process(target = main,args=(q,))
##    p.start()
##    while True:
##        try:
##            print(q.get())
##        except:
##            print("***")
    main()
    os.system("pause")

    
##    import profile
##    profile.run('main()')
   
