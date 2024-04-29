import argparse
import logging
import sys

from control_unit import ControlUnit
from datapath import Datapath
from isa import read_code
from memory_unit import Cache, MemoryUnit


def main(args):
    code = read_code(args.source)

    cache = Cache(64)
    memory = MemoryUnit(args.io_adr, args.mem_size, code, [*args.buffer], cache)
    datapath = Datapath(args.start_adr, memory)
    control = ControlUnit(datapath, memory)

    output, ticks, miss_rate = control.simulate(args.tick_limit)
    logging.info("Cache miss rate: %.3f%%", miss_rate * 100)
    logging.info("%s", f"Ticks: {ticks}\n{output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Basic stack machine emulator", epilog="It's a miracle it actually runs!"
    )

    parser.add_argument("source", metavar="SOURCE", help="a json file containing code to run")
    parser.add_argument(
        "-i",
        "--input",
        dest="buffer",
        type=str,
        metavar="INPUT",
        required=False,
        default="",
        help="an input buffer to pass as IO device input",
    )
    parser.add_argument(
        "-t",
        "--ticks",
        dest="tick_limit",
        type=int,
        metavar="TICKS",
        required=False,
        default=100000,
        help="limit to number of ticks",
    )
    parser.add_argument(
        "-m",
        "--memory",
        dest="mem_size",
        type=int,
        metavar="MEM_SIZE",
        required=False,
        default=1024,
        help="size of internal memory",
    )
    parser.add_argument(
        "-s",
        "--start-adr",
        dest="start_adr",
        type=int,
        metavar="START_ADR",
        required=False,
        default=10,
        help="an address from which the program exectuion starts (first in PC)",
    )
    parser.add_argument(
        "-d",
        "--device-adr",
        dest="io_adr",
        type=int,
        metavar="IO_ADR",
        required=False,
        default=0,
        help="an address mapped to the IO device",
    )
    parser.add_argument(
        "-j",
        "--journal",
        dest="journal",
        action="store_true",
        required=False,
        help="whether to output execution journal: machine's state on every tick. WARNING!: This output can be very long",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        dest="out_file",
        metavar="OUT",
        required=False,
        help="file to store output in. Intercepts journal from stdout if -j is specified",
    )

    args = parser.parse_args()
    logging.addLevelName(logging.DEBUG, "JRNL")
    logging.addLevelName(logging.WARNING, "WARN")
    formatter = logging.Formatter("[%(levelname)s] %(message)s")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG if args.journal and not args.out_file else logging.INFO)
    logger.addHandler(stdout_handler)
    if args.out_file:
        file_handler = logging.FileHandler(args.out_file, mode="w", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG if args.journal else logging.INFO)
        logger.addHandler(file_handler)

    main(args)
