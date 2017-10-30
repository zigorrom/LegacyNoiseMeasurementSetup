from enum import Enum, IntEnum, unique

import modern_agilent_u2542a as daq

@unique
class PGA_GAINS(IntEnum):
    PGA_1 = 1
    PGA_10 = 10
    PGA_100 = 100
    
    @classmethod
    def default_gain(cls):
        return cls.PGA_1


@unique
class FILTER_CUTOFF_FREQUENCIES(IntEnum):
    F0 = 0
    F10 = 10
    F20 = 20
    F30 = 30 
    F40 = 40
    F50 = 50
    F60 = 60
    F70 = 70
    F80 = 80
    F90 = 90
    F100 = 100
    F110 = 110
    F120 = 120
    F130 = 130
    F140 = 140
    F150 = 150

    @classmethod
    def default_cutoff_frequency(cls):
        return cls.F0

@unique
class FILTER_GAINS(IntEnum):
    G1 = 1
    G2 = 2
    G3 = 3
    G4 = 4
    G5 = 5
    G6 = 6
    G7 = 7
    G8 = 8
    G9 = 9
    G10 = 10
    G11 = 11
    G12 = 12
    G13 = 13
    G14 = 14
    G15 = 15
    G16 = 16

    @classmethod
    def default_filter_gain(cls):
        return cls.G1

@unique
class CS_HOLD(Enum):
    CS_HOLD_ON = "ON"
    CS_HOLD_OFF = "OFF"

    @classmethod
    def default_cs_hold_state(cls):
        return cls.CS_HOLD_OFF

@unique
class AI_MODES(Enum):
    AC = 0
    DC = 1


@unique
class CONTROL_BITS(Enum):
    AI_SET_PULSE_BIT = daq.DIG_CH504_BIT0
    AI_SET_MODE_BIT = daq.DIG_CH504_BIT1
    AI_ADC_LETCH_PULSE_BIT = daq.DIG_CH504_BIT2
    AO_DAC_LETCH_PULSE_BIT = daq.DIG_CH504_BIT3



FANS_AI_CHANNELS = IntEnum("FANS_AI_CHANNELS", ["AI_CH_{0}".format(ch) for ch in range(1,9,1)])
FANS_AO_CHANNELS = IntEnum("FANS_AO_CHANNELS", ["AO_CH_{0}".format(ch) for ch in range(1,17,1)])
    
def convert_fans_ai_to_daq_channel(fans_channel):
    assert isinstance(fans_channel, FANS_AI_CHANNELS), "Wrong channel!"
    val = fans_channel.value
    div, mod = divmod(val, 4)
    mode = AI_MODES.AC if div == 0 else AI_MODES.DC
    channel = 100 + mod
    return (channel, mode)

def convert_fans_ao_to_daq_channel(fans_channel):
    assert isinstance(fans_channel, FANS_AO_CHANNELS), "Wrong channel!"
    val = fans_channel.value
    div, mod = divmod(val, 8)
    channel = daq.AO_CHANNEL_201 if div == 0 else daq.AO_CHANNEL_202
    selected_output = mod
    return (channel, selected_output)

def get_filter_value(filter_gain, filter_cutoff):
    assert isinstance(filter_gain, FILTER_GAINS)
    assert isinstance(filter_cutoff, FILTER_CUTOFF_FREQUENCIES)
    return (filter_gain.value<<4)|filter_cutoff.value

def get_pga_value(pga_gain, cs_hold):
    assert isinstance(pga_gain, PGA_GAINS)
    assert isinstance(cs_hold, CS_HOLD)
    return (cs_hold.value << 2) | pga_gain.value

class FANS_AI_CHANNEL:
    def __init__(self, name, parent_device, **kwargs):
        self._name = name
        self._daq_device = parent_device
        self._enabled = daq.SWITCH_STATE_OFF
        self._range = daq.RANGE_10
        self._polarity = daq.BIPOLAR
        self._mode = AI_MODES.DC
        self._cs_hold = CS_HOLD.CS_HOLD_OFF
        self._filter_cutoff = FILTER_CUTOFF_FREQUENCIES.F0
        self._filter_gain = FILTER_GAINS.G1
        self._pga_gain = PGA_GAINS.PGA_1
        

        self.initialize_channel(kwargs)


    def initialize_channel(self, enabled = daq.SWITCH_STATE_OFF, range_val = daq.RANGE_10, polarity = daq.BIPOLAR, mode = AI_MODES.DC, cs_hold = CS_HOLD.CS_HOLD_OFF, filter_cutoff = FILTER_CUTOFF_FREQUENCIES.F0, filter_gain = FILTER_GAINS.G1, pga_gain = PGA_GAINS.PGA_1):
        self._enabled = enabled
        self._range = range_val
        self._polarity = polarity
        self._mode = mode
        self._cs_hold = cs_hold
        self._filter_cutoff = filter_cutoff
        self._filter_gain = filter_gain
        self._pga_gain = pga_gain

    

    def apply_fans_ai_channel_params(self):
        raise NotImplementedError()

        self._parent_device.dig_write_channel(self.ai_name, DIGITAL_CHANNELS.DIG_502)

        self._parent_device.dig_write_bit_channel(self.ai_mode,AI_SET_MODE_BIT,DIGITAL_CHANNELS.DIG_504)#AI_MODE_VAL[mode]
        self._parent_device.pulse_digital_bit(AI_SET_MODE_PULS_BIT,DIGITAL_CHANNELS.DIG_504)
        
            
        ## set filter frequency and gain parameters
        filter_val = get_filter_value(self.ai_filter_gain,self.ai_filter_cutoff)
        print("filter value {0:08b}".format(filter_val))
        self._parent_device.dig_write_channel(filter_val,DIGITAL_CHANNELS.DIG_501)

        ## set pga params
        pga_val = get_pga_value(self.ai_pga_gain,self.ai_cs_hold)
        print("pga value {0:08b}".format(pga_val))
        self._parent_device.dig_write_channel(pga_val, DIGITAL_CHANNELS.DIG_503)
        self._parent_device.pulse_digital_bit(AI_ADC_LETCH_PULS_BIT,DIGITAL_CHANNELS.DIG_504)
        

    @property        
    def ai_amplification(self):
        return self.ai_filter_gain * self.ai_pga_gain if self.ai_mode == AI_MODES.AC else 1

    @property
    def ai_name(self):
        return self.ai_name
    
    @ai_name.setter
    def ai_name(self,value):
        self._name = value

    @property
    def ai_enabled(self):
        return self._enabled
    
    @ai_enabled.setter
    def ai_enabled(self,value):
        self._enabled = value
        #self._parent_device.daq_set_enable_ai_channel(self.ai_enabled,self.ai_name)

    @property
    def ai_range(self):
        return self._range
    
    @ai_range.setter
    def ai_range(self,value):
        self._range = value
        #self._parent_device.daq_set_channel_range(self.ai_range,self.ai_name)

    @property
    def ai_polarity(self):
        return self._polarity
    
    @ai_polarity.setter
    def ai_polarity(self,value):
        self._polarity = value
        #self._parent_device.daq_set_ai_channel_polarity(self.ai_polarity,self.ai_name)
    
    @property
    def ai_mode(self):
        return self._mode
    
    @ai_mode.setter
    def ai_mode(self,value):
        self._mode = value
        
    
    @property
    def ai_cs_hold(self):
        return self._cs_hold
    
    @ai_cs_hold.setter
    def ai_cs_hold(self,value):
        self._cs_hold = value

    @property
    def ai_filter_cutoff(self):
        return self._filter_cutoff

    @ai_filter_cutoff.setter
    def ai_filter_cutoff(self,value):
        self._filter_cutoff = value
        
    @property
    def ai_filter_gain(self):
        return self._filter_gain

    @ai_filter_gain.setter
    def ai_filter_gain(self,value):
        self._filter_gain = value
       
    @property
    def ai_pga_gain(self):
        return self._pga_gain

    @ai_pga_gain.setter
    def ai_pga_gain(self,value):
        self._pga_gain = value
       
class FANS_CONTROLLER:
    def __init__(self):
        self.daq_device = None
        #self.fans_ai_channels = {ch: FANS_AI_CHANNEL(ch, self) for ch in FANS_AI_CHANNELS}


    def initialize_hardware(self, resource):
        assert isinstance(resource, str), "Wrong resource type!"
        self.daq_device = daq.AgilentU2542A_DSP(resource)
        
        # initialize all digital channels as output for control
        self.daq_device.set_digital_mode_for_channels(daq.DIG_CHANNELS, daq.DIGITAL_MODE_OUTPUT)

    def digital_write(self, value, channel):
        self.daq_device.digital_write(channel, value)
    
    def digital_write_bit(self, value, bit):
        self.daq_device.digital_write_bit(bit, value)

    def digital_pulse_bit(self, bit):
        self.daq_device.digital_pulse_bit(bit)
    
    




if __name__ == "__main__":
    #print(PGA_GAINS.PGA_2 in PGA_GAINS)
    #ch = convert_fans_ai_to_daq_channel(FANS_AI_CHANNELS.AI_CH_6)
    
    #print(ch)

    c = FANS_CONTROLLER()