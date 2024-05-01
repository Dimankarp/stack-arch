import contextlib
import io
import logging
import os
import tempfile

import forthc
import machine
import pytest


@pytest.mark.golden_test("tests/*.yml")
def test_forthc_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.f")
        target = os.path.join(tmpdirname, "target.o")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        forthc_commands = [*golden["in_forthc_options"].split(), source, target]
        machine_commands = [*golden["in_machine_options"].split(), "-i", golden["in_stdin"], target]
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            forthc_args = forthc.parser.parse_args(forthc_commands)
            forthc.main(forthc_args)
            print("=" * 60)
            machine_args = machine.parser.parse_args(machine_commands)
            machine.main(machine_args)

        with open(target, encoding="utf-8") as file:
            code = file.read()
        log_blocks = caplog.text.split("\n\n")
        if len(log_blocks) < 150:
            log = caplog.text
        else:
            log = "\n\n".join(
                [
                    *log_blocks[0:50],
                    ".....",
                    *log_blocks[len(log_blocks) // 2 - 25 : len(log_blocks) // 2 + 25],
                    ".....",
                    *log_blocks[-50:],
                ]
            )
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert log == golden.out["out_log"]
