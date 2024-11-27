#
# ????
#

from enum import Enum, unique


@unique
class MessageTypes(Enum):
    CMD = 'command'
    REPLY = 'reply'
    ERROR = 'error'
    HALT = 'halt'

@unique
class Commands(Enum):
    START = 'start'
    STOP = 'stop'
    SET = 'set'
    GET = 'get'
    SCAN = 'scan'
    LASER = 'laser'
    VERSION = 'version'
