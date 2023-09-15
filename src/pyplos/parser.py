from __future__ import annotations

import operator

from dataclasses import dataclass
from functools import partial

from . import token
from .util import pluck, select


class Command:
    @staticmethod
    def parse(tape):
        raise NotImplementedError


@dataclass
class Search(Command):
    source: str

    @staticmethod
    def parse(tape):
        tape.next(value="source")
        tape.next(value="=")
        source = parse_identifier(tape).name

        return Search(source=source)


@dataclass
class Where(Command):
    expr: ...

    @staticmethod
    def parse(tape):
        return Where(parse_boolean(tape))

    def execute(self, table):
        return [row for row in table if self.expr.eval(row)]


@dataclass
class Fields(Command):
    columns: list

    @staticmethod
    def parse(tape):
        columns = [parse_identifier(tape).name]

        while tape.next_if(value=","):
            columns.append(parse_identifier(tape).name)

        return Fields(columns)

    def execute(self, table):
        return list(map(partial(select, self.columns), table))


@dataclass
class Head(Command):
    n: int

    @staticmethod
    def parse(tape):
        token_ = tape.next_if(type=token.Number)

        if token_ is not None:
            n = token_.unwrap()
        else:
            n = 5

        return Head(n=n)

    def execute(self, table):
        return table[: self.n]


@dataclass
class Stats(Command):
    aggregations: list[Aggregation]
    by: list[str]

    @staticmethod
    def parse(tape):
        aggregations = [parse_aggregation(tape)]

        while tape.next_if(value=","):
            aggregations.append(parse_aggregation(tape))

        by = None
        if tape.next_if(value="by"):
            by = [parse_identifier(tape).name]

            while tape.next_if(value=","):
                by.append(parse_identifier(tape).name)

        return Stats(aggregations, by)

    def execute(self, table):
        return [
            {str(aggregation): aggregation.eval(table)}
            for aggregation in self.aggregations
        ]


class BoolExpr:
    pass


comparisons = {
    "<": operator.lt,
    "<=": operator.le,
    "=": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    ">": operator.gt,
}


@dataclass
class Comparison(BoolExpr):
    op: str
    left: token.Token
    right: token.Token

    def eval(self, row):
        op = comparisons[self.op]

        return op(self.left.eval(row), self.right.eval(row))


@dataclass
class And(BoolExpr):
    left: BoolExpr
    right: BoolExpr

    def eval(self, row):
        return self.left.eval() and self.right.eval()


@dataclass
class Or(BoolExpr):
    left: BoolExpr
    right: BoolExpr

    def eval(self, row):
        return self.left.eval(row) or self.right.eval(row)


@dataclass
class Aggregation:
    stat: str
    field: str

    def __str__(self):
        return f"{self.stat}({self.field})"

    def eval(self, rows):
        functions = {"avg": lambda values: sum(values) / len(values)}

        return functions[self.stat](pluck(self.field, rows))


commands = {
    "search": Search,
    "where": Where,
    "fields": Fields,
    "head": Head,
    "stats": Stats,
}


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


def parse_identifier(tape):
    return tape.next(type=(token.Name, token.Identifier))


def parse_value(tape):
    return tape.next(type=(token.Name, token.Identifier, token.Number, token.String))


def parse_command(tape):
    name = tape.next(type=token.Name).name

    command = commands[name]
    return command.parse(tape)


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
        return Or(left, parse_and(tape))

    else:
        return left


def parse_and(tape):
    left = parse_comparison(tape)

    if tape.next_if(value="and"):
        right = parse_comparison(tape)

        return And(left, right)

    else:
        return left


def parse_comparison(tape):
    left = parse_value(tape)

    op = tape.next().value
    assert op in {"=", "!=", "<", "<=", ">", ">="}

    right = parse_value(tape)

    return Comparison(op, left, right)


def parse_aggregation(tape):
    aggregation = parse_identifier(tape).name
    tape.next(value="(")
    field = parse_identifier(tape).name
    tape.next(value=")")

    return Aggregation(aggregation, field)
