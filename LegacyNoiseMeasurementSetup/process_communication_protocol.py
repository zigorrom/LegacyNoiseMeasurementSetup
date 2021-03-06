﻿from n_enum import enum

ExperimentCommands = enum("EXPERIMENT_STARTED","EXPERIMENT_STOPPED","DATA","MESSAGE", "MEASUREMENT_STARTED", "MEASUREMENT_FINISHED", "SPECTRUM_DATA", "TIMETRACE_DATA","EXPERIMENT_INFO", "MEASUREMENT_INFO","MEASUREMENT_INFO_START","MEASUREMENT_INFO_END", "ABORT", "ERROR", "LOG_MESSAGE")

COMMAND = 'c'
PARAMETER = 'p'
DATA = 'd'
AVERAGES = 'avg'
SPECTRUM_RANGE = 'r'
FREQUENCIES = 'f'
INDEX = 'i'
