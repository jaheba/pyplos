from __future__ import annotations

import re

from dataclasses import dataclass

from .util import first, valfilter


def one_of(*xs):
    return "[%s]" % "".join(map(re.escape, xs))


@dataclass
class Token:
    match: re.Match

    _subtokens = []

    def __init_subclass__(cls):
        Token._subtokens.append(cls)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    @property
    def value(self):
        return self.match.string[slice(*self.match.span())]

    @staticmethod
    def ize(raw: str):
        classes = {cls.__name__: cls for cls in Token._subtokens}

        rx = "|".join(rf"(?P<{cls.__name__}>{cls.rx})" for cls in Token._subtokens)

        tokens = []
        for match in re.finditer(rx, raw):
            name, raw = first(
                valfilter(lambda val: val is not None, match.groupdict()).items()
            )

            if name == "Any":
                raise ValueError(f"Can't parse {raw!r}")
            elif name == "Space":
                continue

            token = classes[name](match)
            tokens.append(token)

        return tokens


class Number(Token):
    rx = r"\d+"

    def unwrap(self):
        return int(self.value)

    def eval(self, data):
        return self.unwrap()


class String(Token):
    rx = r'"(?:[^"\\]|\\.)*"'

    def unwrap(self):
        return self.value[1:-1]

    def eval(self, data):
        return self.unwrap()


class Name(Token):
    rx = r"\w+"

    def eval(self, data):
        return data[self.value]

    @property
    def name(self):
        return self.value


class Identifier(Token):
    rx = r"`.+?`"

    def eval(self, data):
        return data[self.value.strip("`")]

    @property
    def name(self):
        return self.value.strip("`")


class Pipe(Token):
    rx = r"\|"


class Parenthesis(Token):
    rx = r"[()]"


class Space(Token):
    rx = r"\s+"


class Operator(Token):
    rx = one_of("+", "-", "*", "/", ">=", "<=", "=", ">", "<", ",")


class End(Token):
    rx = r";"


class Any(Token):
    rx = r".+?"
