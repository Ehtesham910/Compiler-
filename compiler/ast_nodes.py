from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union


class Node:
    pass


class Stmt(Node):
    pass


class Expr(Node):
    pass


@dataclass(frozen=True)
class Program(Node):
    statements: List[Stmt]


@dataclass(frozen=True)
class Block(Node):
    statements: List[Stmt]


@dataclass(frozen=True)
class VarDecl(Stmt):
    name: str
    expr: Expr


@dataclass(frozen=True)
class Assign(Stmt):
    name: str
    expr: Expr


@dataclass(frozen=True)
class Print(Stmt):
    expr: Expr


@dataclass(frozen=True)
class If(Stmt):
    cond: Expr
    then_block: Block
    else_block: Optional[Block]


@dataclass(frozen=True)
class While(Stmt):
    cond: Expr
    body: Block


@dataclass(frozen=True)
class For(Stmt):
    init: Optional[Stmt]
    cond: Optional[Expr]
    incr: Optional[Stmt]
    body: Block


@dataclass(frozen=True)
class Switch(Stmt):
    expr: Expr
    cases: List['Case']
    default: Optional[Block]


@dataclass(frozen=True)
class Case(Stmt):
    value: Expr
    body: Block


@dataclass(frozen=True)
class Break(Stmt):
    pass


@dataclass(frozen=True)
class Continue(Stmt):
    pass


@dataclass(frozen=True)
class Literal(Expr):
    value: Union[int, float, str]


@dataclass(frozen=True)
class VarRef(Expr):
    name: str


@dataclass(frozen=True)
class Unary(Expr):
    op: str  # "!" or "-" (unary minus)
    expr: Expr


@dataclass(frozen=True)
class Binary(Expr):
    op: str  # "+", "-", "*", "/", "%", comparisons, "&&", "||"
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Ternary(Expr):
    cond: Expr
    true_expr: Expr
    false_expr: Expr


@dataclass(frozen=True)
class Read(Expr):
    pass

