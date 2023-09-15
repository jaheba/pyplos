from __future__ import annotations

import operator

from dataclasses import dataclass
from functools import partial

from . import token
from .util import pluck, select


class Command:
    pass


@dataclass
class Search(Command):
    source: str


@dataclass
class Where(Command):
    expr: ...

    def execute(self, table):
        return [row for row in table if self.expr.eval(row)]


@dataclass
class Fields(Command):
    columns: list

    def execute(self, table):
        return list(map(partial(select, self.columns), table))


@dataclass
class Head(Command):
    n: int

    def execute(self, table):
        return table[: self.n]


@dataclass
class Stats(Command):
    aggregations: list[Aggregation]
    by: list[str]

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
