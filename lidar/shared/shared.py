#
# ????
#

from enum import Enum, unique


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
    VERSION = 'version'
