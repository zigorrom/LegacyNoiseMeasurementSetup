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
    DC = 0
    AC = 1


@unique
class CONTROL_BITS(Enum):
    AI_SET_MODE_PULSE_BIT = daq.DIG_CH504_BIT0
    AI_SET_MODE_BIT = daq.DIG_CH504_BIT1
    AI_ADC_LETCH_PULSE_BIT = daq.DIG_CH504_BIT2
    AO_DAC_LETCH_PULSE_BIT = daq.DIG_CH504_BIT3



FANS_AI_CHANNELS = IntEnum("FANS_AI_CHANNELS", ["AI_CH_{0}".format(ch) for ch in range(1,9,1)])
FANS_AO_CHANNELS = IntEnum("FANS_AO_CHANNELS", ["AO_CH_{0}".format(ch) for ch in range(1,17,1)])
    
def convert_fans_ai_to_daq_channel(fans_channel):
    assert isinstance(fans_channel, FANS_AI_CHANNELS), "Wrong channel!"
    val = fans_channel.value
    div, mod = divmod(val, 4)
    mode = AI_MODES.DC if div == 0 else AI_MODES.AC
    channel = 100 + mod
    return (channel, mode)

def convert_daq_ai_to_fans_channel(daq_channel, mode):
    assert daq_channel in daq.AI_CHANNELS, "Channel is not in the list"
    assert isinstance(mode, AI_MODES)
    mod = daq_channel - 100
    div = 0 if mode == AI_MODES.DC else 1
    fans_channel = FANS_AI_CHANNELS(div*4+mod)
    return fans_channel

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
    def __init__(self, daq_input, parent_device, **kwargs):
        assert isinstance(parent_device, FANS_CONTROLLER), "parent device has wrong type"
        assert daq_input in daq.AI_CHANNELS , "wrong channel number"
        #assert selected_daq_input in daq.AI_CHANNELS
        #self._name = name
        self._daq_input = daq_input
        self._fans_device = parent_device

        self._enabled = daq.SWITCH_STATE_OFF
        self._range = daq.RANGE_10
        self._polling_range = daq.AUTO_RANGE
        self._polarity = daq.BIPOLAR
        self._polling_polarity = daq.BIPOLAR
        
        self._mode = AI_MODES.DC
        self._cs_hold = CS_HOLD.CS_HOLD_OFF
        self._filter_cutoff = FILTER_CUTOFF_FREQUENCIES.F0
        self._filter_gain = FILTER_GAINS.G1
        self._pga_gain = PGA_GAINS.PGA_1
        
        #self.initialize_channel(**kwargs)

    @property
    def ai_enabled(self):
        return self._enabled

    def ai_enabled(self, state):
        assert state in daq.SWITCH_STATES , "Wrong value of state"
        self._enabled = state
        self.fans_controller.switch_daq_channel_enabled(self.ai_daq_input, state)
        

    def __str__(self, **kwargs):
        return str(self.ai_daq_input, **kwargs)

    def initialize_channel(self, enabled = daq.SWITCH_STATE_OFF, range_val = daq.RANGE_10, polarity = daq.BIPOLAR, mode = AI_MODES.DC, cs_hold = CS_HOLD.CS_HOLD_OFF, filter_cutoff = FILTER_CUTOFF_FREQUENCIES.F0, filter_gain = FILTER_GAINS.G1, pga_gain = PGA_GAINS.PGA_1):
        self._enabled = enabled
        self._range = range_val
        self._polarity = polarity
        self._mode = mode
        self._cs_hold = cs_hold
        self._filter_cutoff = filter_cutoff
        self._filter_gain = filter_gain
        self._pga_gain = pga_gain

    def apply_acquisition_hardware_params(self):
        pass
        #device = self._fans_device
        #device.switch_daq_ai_channel_enabled(self.ai_daq_input, self.ai_enabled)
        #device.set_acquisition_daq_range(self.ai_daq_input, self.ai_range)
        #device.set_acquisition_polarity(self.ai_daq_input, self.ai_polarity)

    def apply_acquisition_params(self):
        pass

    def apply_polling_hardware_params(self):
        pass

    def apply_fans_ai_channel_params(self):
        #raise NotImplementedError()
        device = self._daq_device    
        device.digital_write(self.ai_daq_input, daq.DIG_CHANNEL_502)

        device.digital_write_bit(self.ai_mode.value, CONTROL_BITS.AI_SET_MODE_BIT)
        device.digital_pulse_bit(CONTROL_BITS.AI_SET_MODE_PULSE_BIT)

        filter_val = get_filter_value(self.ai_filter_gain, self.ai_filter_cutoff)
        print("filter value {0:08b}".format(filter_val))
        device.digital_write(filter_val, daq.DIG_CHANNEL_501)

        pga_val = get_pga_value(self.ai_pga_gain,self.ai_cs_hold)
        print("pga value {0:08b}".format(pga_val))
        device.digital_write(pga_val, daq.DIG_CHANNEL_503)

        device.digital_pulse_bit(CONTROL_BITS.AI_ADC_LETCH_PULSE_BIT)
        
    @property
    def fans_controller(self):
        return self._fans_device

    @property
    def ai_daq_input(self):
        return self._daq_input

    @property        
    def ai_amplification(self):
        return self.ai_filter_gain.value * self.ai_pga_gain.value if self.ai_mode == AI_MODES.AC else 1
    
    @property
    def ai_mode(self):
        return self._mode
        
    @property
    def ai_cs_hold(self):
        return self._cs_hold
    
    @property
    def ai_filter_cutoff(self):
        return self._filter_cutoff
        
    @property
    def ai_filter_gain(self):
        return self._filter_gain

    @property
    def ai_pga_gain(self):
        return self._pga_gain
    
    def analog_read(self):
        return self.fans_controller.analog_read(self.ai_daq_input)




class FANS_AI_MULTICHANNEL:
    def __init__(self, *args):
        assert len(args) > 0, "Too less channels to create multichannel"
        assert all(isinstance(channel, FANS_AI_CHANNEL) for channel in args), "At least one channels has wrong type!"
        fans_controller = args[0].fans_controller
        assert all(fans_controller is channel.fans_controller for channel in args), "Not all channels reference same fans controller!"
        self._fans_controller = fans_controller
        self._fans_channels = list(args)


    @property
    def fans_channels(self):
        return self._fans_channels

    @property
    def fans_controller(self):
        return self._fans_controller

    @property
    def daq_channels(self):
        daq_ch = [channel.ai_daq_input for channel in self.fans_channels]
        return daq_ch

    def analog_read(self):
        return self.fans_controller.analog_read_for_channels(self.daq_channels)

class FANS_AO_CHANNEL:
    def __init__(self, daq_output, parent_device, **kwargs):
        assert isinstance(parent_device, FANS_CONTROLLER), "parent device has wrong type"
        assert daq_output in daq.AO_CHANNELS , "wrong channel number"
        self._fans_device = parent_device
        self._daq_output = daq_output
        self._enabled = None
        self._ao_polarity = None
        self._voltage = 0

    @property
    def fans_controller(self):
        return self._fans_device

    @property
    def ao_daq_output(self):
        return self._daq_output

    def apply_dac_hardware_params(self):
        pass

    def apply_fans_ao_channel_params(self):
        pass

    def analog_write(self, voltage):
        self.fans_controller.analog_source_voltage(self.ao_daq_output, voltage)



class FANS_AO_MULTICHANNEL:
    def __init__(self, *args):
        assert len(args) > 0, "Too less channels to create multichannel"
        assert all(isinstance(channel, FANS_AO_CHANNEL) for channel in args), "At least one channels has wrong type!"
        fans_controller = args[0].fans_controller
        assert all(fans_controller is channel.fans_controller for channel in args), "Not all channels reference same fans controller!"
        self._fans_controller = fans_controller
        self._fans_channels = list(args)
 
    @property
    def fans_channels(self):
        return self._fans_channels

    @property
    def fans_controller(self):
        return self._fans_controller

    @property
    def daq_channels(self):
        daq_ch = [ch.ao_daq_output for ch in self.fans_channel]
        return daq_ch

    def analog_write(self, voltage):
        self.fans_controller.analog_source_voltage_for_channels(self.daq_channels, voltage)


   
class FANS_CONTROLLER:
    def __init__(self):
        self.daq_device = None
        ai_mode = AI_MODES.AC
        self._fans_ai_channels = {ch: FANS_AI_CHANNEL(ch, self) for ch in daq.AI_CHANNELS}
        self._fans_ao_channels = {ch: FANS_AO_CHANNEL(ch,self) for ch in daq.AO_CHANNELS}

    @property
    def fans_ao_channels(self):
        return self._fans_ao_channels

    @property
    def fans_ai_channels(self):
        return self._fans_ai_channels

    @property
    def daq_parent_device(self):
        return self.daq_device


    def initialize_hardware(self, resource):
        assert isinstance(resource, str), "Wrong resource type!"
        self.daq_device = daq.AgilentU2542A_DSP(resource)
        
        # initialize all digital channels as output for control
        self.set_digital_channels_to_control_mode()



    def set_digital_channels_to_control_mode(self):
        self.daq_device.set_digital_mode_for_channels(daq.DIG_CHANNELS, daq.DIGITAL_MODE_OUTPUT)

    def digital_write(self, value, channel):
        self.daq_device.digital_write(channel, value)
    
    def digital_write_bit(self, value, bit):
        self.daq_device.digital_write_bit(bit, value)

    def digital_pulse_bit(self, bit):
        self.daq_device.digital_pulse_bit(bit)
    
    def switch_daq_channel_enabled(self, channel, state):
        self.daq_device.switch_enabled(channel, state)

    def switch_daq_enabled_for_channels(self, channels, state):
        self.daq_device.switch_enabled_for_channels(channels, state)

    def set_acquisition_daq_range(self, channel, range_val):
        self.daq_device.set_range(channel, range_val)

    def set_acquisition_daq_range_for_channels(self, channels, range_val):
        self.daq_device.set_range_for_channels(channels, range_val)

    def set_acquisition_polarity(self, channel, polarity):
        self.daq_device.set_polarity(channel, polarity)

    def set_acquisition_polarity_for_channels(self, channels, polarity):
        self.daq_device.set_polarity_for_channels(channels, polarity)

    def set_analog_range(self, channel, range_val):
        self.daq_device.analog_set_range(channel, range_val)

    def set_analog_range(self, channels, range_val):
        self.daq_device.analog_set_range_for_channels(channels, range_val)

    def set_analog_polarity(self, channel, polarity):
        self.daq_device.analog_set_polarity(channel, polarity)

    def set_analog_polarity_for_channels(self, channels, polarity):
        self.daq_device.analog_set_polarity_for_channels(channels, polarity)

    def set_analog_source_polarity(self, channel, polarity):
        self.daq_device.analog_set_source_polarity(channel, polarity)

    def set_analog_source_polarity_for_channels(self, channels, polarity):
        self.daq_device.analog_set_source_polarity_for_channels(channels, polarity)

    def analog_read(self, channel):
        return self.daq_device.analog_measure(channel)

    def analog_read_for_channels(self, channels):
        return self.daq_device.analog_measure_channels(channels)

    def analog_source_voltage(self, channel, voltage):
        self.daq_device.analog_source_voltage(channel, voltage)

    def analog_source_voltage_for_channels(self, channels, voltage):
        self.daq_device.analog_source_voltage_for_channels(channels, voltage)

    def switch_output_on(self):
        self.daq_device.analog_set_output_state(daq.SWITCH_STATE_ON)

    def switch_output_off(self):
        self.daq_device.analog_set_output_state(daq.SWITCH_STATE_OFF)

    def set_analog_read_averaging(self, averaging):
        self.daq_device.analog_set_averaging(averaging)

    def query_analog_read_averaging(self):
        return self.daq_device.analog_averaging_query()


if __name__ == "__main__":
    #print(PGA_GAINS.PGA_2 in PGA_GAINS)
    #ch = convert_fans_ai_to_daq_channel(FANS_AI_CHANNELS.AI_CH_6)
    
    #print(ch)

    c = FANS_CONTROLLER()
    ch1 = c.fans_ai_channels[daq.AI_CHANNEL_101]
    ch2 = c.fans_ai_channels[daq.AI_CHANNEL_102]
    ch3 = c.fans_ai_channels[daq.AI_CHANNEL_103]
    ch4 = c.fans_ai_channels[daq.AI_CHANNEL_104]

    mc = FANS_AI_MULTICHANNEL(ch1, ch2,ch3)
    print(mc.daq_channels)
    
    #print(convert_daq_ai_to_fans_channel(daq.AI_CHANNEL_101, AI_MODES.AC))
    #print(convert_daq_ai_to_fans_channel(daq.AI_CHANNEL_101, AI_MODES.DC))
    #print(convert_daq_ai_to_fans_channel(daq.AI_CHANNEL_104, AI_MODES.AC))
    #print(convert_daq_ai_to_fans_channel(daq.AI_CHANNEL_104, AI_MODES.DC))
