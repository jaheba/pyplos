from __future__ import annotations

import operator
from collections import defaultdict
from dataclasses import dataclass
from functools import partial, cmp_to_key
from typing import Optional

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
        if self.by:
            groups = defaultdict(list)

            for row in table:
                groups[tuple(row[column] for column in self.by)].append(row)

            return [
                {
                    str(aggregation): aggregation.eval(group),
                    **dict(zip(self.by, group_key)),
                }
                for group_key, group in groups.items()
                for aggregation in self.aggregations
            ]

        return [
            {str(aggregation): aggregation.eval(table)}
            for aggregation in self.aggregations
        ]


def multi_compare(columns):
    def compare(xs, ys):
        for column, order in columns:
            x = xs[column]
            y = ys[column]

            if x == y:
                continue

            if x < y:
                if order == "-":
                    return 1
                return -1
            else:
                if order == "-":
                    return -1
                return 1

        return 0

    return compare


@dataclass
class Sort(Command):
    columns: list

    def execute(self, table):
        table = sorted(table, key=cmp_to_key(multi_compare(self.columns)))

        return table


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
        return self.left.eval(row) and self.right.eval(row)


@dataclass
class Or(BoolExpr):
    left: BoolExpr
    right: BoolExpr

    def eval(self, row):
        return self.left.eval(row) or self.right.eval(row)


@dataclass
class Aggregation:
    stat: str
    field: Optional[str]

    def __str__(self):
        field = self.field or ""

        return f"{self.stat}({field})"

    def eval(self, rows):
        if self.stat == "count":
            return len(rows)

        functions = {
            "avg": lambda values: sum(values) / len(values),
            "min": min,
            "max": max,
        }

        return functions[self.stat](pluck(self.field, rows))
