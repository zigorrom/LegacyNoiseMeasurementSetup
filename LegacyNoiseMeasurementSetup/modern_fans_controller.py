from enum import Enum, unique

import modern_agilent_u2542a as daq

@unique
class PGA_GAINS(Enum):
    PGA_1 = 1
    PGA_10 = 10
    PGA_100 = 100
    
    @classmethod
    def default_gain(cls):
        return cls.PGA_1


@unique
class FILTER_CUTOFF_FREQUENCIES(Enum):
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
class FILTER_GAINS(Enum):
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



if __name__ == "__main__":
    #print(PGA_GAINS.PGA_2 in PGA_GAINS)
    
    assert isinstance(PGA_GAINS(10), PGA_GAINS), "afasfasf"
    #print(PGA_GAINS.PGA_1.value)