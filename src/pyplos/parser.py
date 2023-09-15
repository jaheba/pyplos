from __future__ import annotations


from dataclasses import dataclass

from . import ast
from . import token


@dataclass
class Tape:
    xs: list
    index: int = 0

    def __len__(self):
        return len(self.xs) - self.index

    def peek(self):
        return self.xs[self.index]

    def next(self, *, type=None, value=None):
        assert self, "End of tape."

        token = self.xs[self.index]

        if type is not None:
            assert isinstance(token, type)

        if value is not None:
            assert token.value == value, f"{token.value!r} != {value!r}"

        self.index += 1
        return token

    def next_if(self, *, type=None, value=None, default=None):
        try:
            return self.next(type=type, value=value)
        except Exception:
            return default


def parse_search(tape):
    tape.next(value="source")
    tape.next(value="=")
    source = parse_identifier(tape).name

    return ast.Search(source=source)


def parse_where(tape):
    return ast.Where(parse_boolean(tape))


def parse_fields(tape):
    columns = [parse_identifier(tape).name]

    while tape.next_if(value=","):
        columns.append(parse_identifier(tape).name)

    return ast.Fields(columns)


def parse_head(tape):
    token_ = tape.next_if(type=token.Number)

    if token_ is not None:
        n = token_.unwrap()
    else:
        n = 5

    return ast.Head(n=n)


def parse_stats(tape):
    aggregations = [parse_aggregation(tape)]

    while tape.next_if(value=","):
        aggregations.append(parse_aggregation(tape))

    by = None
    if tape.next_if(value="by"):
        by = [parse_identifier(tape).name]

        while tape.next_if(value=","):
            by.append(parse_identifier(tape).name)

    return ast.Stats(aggregations, by)


def parse_identifier(tape):
    return tape.next(type=(token.Name, token.Identifier))


def parse_value(tape):
    return tape.next(type=(token.Name, token.Identifier, token.Number, token.String))


def parse_command(tape):
    commands = {
        "search": parse_search,
        "where": parse_where,
        "fields": parse_fields,
        "head": parse_head,
        "stats": parse_stats,
    }

    name = tape.next(type=token.Name).name
    return commands[name](tape)


def parse_ppl(raw: str):
    tokens = token.Token.ize(raw)
    tape = Tape(tokens)

    search = parse_command(tape)
    # assert isinstance(search, Search)

    commands = [search]

    while tape and not tape.next_if(value=";"):
        tape.next(value="|")
        commands.append(parse_command(tape))

    return commands


def parse_boolean(tape):
    return parse_or(tape)


def parse_or(tape):
    left = parse_and(tape)

    if tape.next_if(value="or"):
        return ast.Or(left, parse_and(tape))

    else:
        return left


def parse_and(tape):
    left = parse_comparison(tape)

    if tape.next_if(value="and"):
        right = parse_comparison(tape)

        return ast.And(left, right)

    else:
        return left


def parse_comparison(tape):
    left = parse_value(tape)

    op = tape.next().value
    assert op in {"=", "!=", "<", "<=", ">", ">="}

    right = parse_value(tape)

    return ast.Comparison(op, left, right)


def parse_aggregation(tape):
    aggregation = parse_identifier(tape).name
    tape.next(value="(")
    field = parse_identifier(tape).name
    tape.next(value=")")

    return ast.Aggregation(aggregation, field)
