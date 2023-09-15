if __name__ == "__main__":
    import json
    import sys

    from .util import tabulate

    from .parser import parse_ppl

    path, *args = sys.argv[1:]

    commands = parse_ppl(" ".join(args))

    with open(path) as infile:
        table = json.loads(infile.read())

    for command in commands:
        table = command.execute(table)

    tabulate(table)
    # print(table[:100])
