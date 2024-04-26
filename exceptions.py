class BufferEmptyError(Exception):
    """Raised when input buffer is empty"""

    def __init__(self):
        super().__init__("Input buffer is empty")


class HaltError(Exception):
    """Raised on halt instruction"""

    def __init__(self):
        super().__init__("Halt instruction was executed")


class InstructionAsDataError(Exception):
    """Raised when instruction is being used as data"""

    def __init__(self, reg: str, instruction):
        super().__init__(f"Instruction is being used as data in {reg}: {instruction}")


class DataAsInstructionError(Exception):
    """Raised when something other than instructions is being interpreted"""

    def __init__(self, reg: str, data):
        super().__init__(f"Data is being used as instruction in {reg}: {data}")


class StackOverflowError(Exception):
    """Raised on stack overflow"""

    def __init__(self):
        super().__init__("Stack overflow")


class StackUnderflowError(Exception):
    """Raised on stack underflow"""

    def __init__(self):
        super().__init__("Stack underflow")


class MicrocodeJumpFailError(Exception):
    """Raised when some goes wrong on the microcode level"""

    def __init__(self):
        super().__init__("Failed to mjump by opcode")
