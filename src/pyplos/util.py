def first(xs):
    return next(iter(xs))


def valmap(fn, dct):
    return {key: fn(value) for key, value in dct.items()}


def valfilter(fn, dct):
    return {key: value for key, value in dct.items() if fn(value)}


def select(keys, dct):
    return {key: dct[key] for key in keys}


def pluck(key, xs):
    return [x[key] for x in xs]


def spaced(value: str, space: int):
    return value + " " * (space - len(value))


def tabulate(table):
    table = [valmap(str, row) for row in table]

    titles = list(table[0])

    max_lengths = {key: len(key) for key in titles}

    for row in table:
        for name, column in row.items():
            max_lengths[name] = max(max_lengths[name], len(column))

    def format_row(row):
        return " | ".join(
            [
                spaced(column, length)
                for column, length in zip(row, max_lengths.values())
            ]
        )

    print(format_row(titles))
    print(format_row(["-" * length for length in max_lengths.values()]))

    for row in table:
        print(format_row(row.values()))
