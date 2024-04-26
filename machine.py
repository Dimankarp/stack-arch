import logging
import sys

from control_unit import ControlUnit
from datapath import Datapath
from isa import read_code
from memory_unit import MemoryUnit


def main(code_file, buffer):
    code = read_code(code_file)

    memory = MemoryUnit(0, 1024, code, [*buffer])
    datapath = Datapath(10, memory)
    control = ControlUnit(datapath, memory)

    output, ticks = control.simulate(100000)
    print(f"{output}\nTicks: {ticks}")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert (
        len(sys.argv) == 3
    ), f"Invalid number of arguments: {len(sys.argv)}. Correct use: machine.py <code_file> <buffer>"

    _, code_file, buffer = sys.argv
    main(code_file, buffer)
