import csv
import json
import re
import sys

from pathlib import Path

from .parser import parse_ppl
from .util import tabulate, valmap


def parse(value):
    if re.match("^\d+$", value):
        return int(value)

    try:
        return float(value)
    except ValueError:
        pass

    return value


def cli():
    path, *args = sys.argv[1:]

    path = Path(path)
    if path.suffix == ".json":
        with open(path) as infile:
            table = json.loads(infile.read())
    elif path.suffix == ".csv":
        with open(path) as infile:
            reader = csv.DictReader(infile)

            table = [valmap(parse, row) for row in reader]
    else:
        raise ValueError(f"Unknown suffix {path.suffix!r}.")

    commands = parse_ppl(" ".join(args))

    for command in commands:
        table = command.execute(table)

    tabulate(table)


if __name__ == "__main__":
    cli()
