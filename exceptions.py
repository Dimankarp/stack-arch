class EOFException(Exception):
    """Raised when input buffer is empty"""

class Halt(Exception):
    """Raised on halt instruction"""

class DataInterpretation(Exception):
    """Raised when something other than instructions is being interpreted"""

class StackExcpetion(Exception):
    """Raised on stack over/underflow"""

class MicrocodeException(Exception):
    """Raised when some goes wrong on the microcode level"""

class TickLimitExceeded(Exception):
    """Raised when ticks exceed limit"""