#
# Shared constants and enums for Lidar package
#

from enum import Enum, unique


MIN_ANGLE = -180.0
MAX_ANGLE = 180.0
MIN_RANGE = 0.02      # meters
MAX_RANGE = 12.0      # meters
MIN_SCAN_FREQ = 6.0   # Hz
MAX_SCAN_FREQ = 12.0  # Hz
MIN_SAMPLE_RATE = 1   # KHz ????
MAX_SAMPLE_RATE = 4   # KHz ????

MIN_ANGLE_RESOLUTION = 0.54  # degrees

MIN_TILT_ANGLE = 0.0   # degrees
DEF_TILT_ANGLE = 0.75  # degrees
MAX_TILT_ANGLE = 1.5   # degrees


@unique
class MessageTypes(Enum):
    CMD = 'command'
    STATUS = 'status'
    REPLY = 'reply'
    ERROR = 'error'
    HALT = 'halt'

@unique
class Commands(Enum):
    INIT = 'init'
    STOP = 'stop'
    SET = 'set'
    GET = 'get'
    SCAN = 'scan'
    LASER = 'laser'
    STREAM = 'stream'
    VERSION = 'version'
