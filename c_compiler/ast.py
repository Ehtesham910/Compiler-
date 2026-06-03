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
    init: Optional[Expr]
    line: int = 0
    col: int = 0


@dataclass(frozen=True)
class Assign(Stmt):
    name: str
    expr: Expr
    line: int = 0
    col: int = 0


@dataclass(frozen=True)
class Print(Stmt):
    expr: Expr
    line: int = 0
    col: int = 0


@dataclass(frozen=True)
class If(Stmt):
    cond: Expr
    then_block: Block
    else_block: Optional[Block]
    line: int = 0
    col: int = 0


@dataclass(frozen=True)
class While(Stmt):
    cond: Expr
    body: Block
    line: int = 0
    col: int = 0


@dataclass(frozen=True)
class Literal(Expr):
    value: int


@dataclass(frozen=True)
class VarRef(Expr):
    name: str
    line: int = 0
    col: int = 0


@dataclass(frozen=True)
class Unary(Expr):
    op: str  # "!" or "-" (unary minus)
    expr: Expr


@dataclass(frozen=True)
class Binary(Expr):
    op: str  # "+ - * / % == != < <= > >= && ||"
    left: Expr
    right: Expr

