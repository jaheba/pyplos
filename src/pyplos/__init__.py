from .parser import parse_ppl


def ppl(query, data):
    commands = parse_ppl(query)

    for command in commands:
        data = command.execute(data)

    return data
