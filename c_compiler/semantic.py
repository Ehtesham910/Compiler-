from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .ast import (
    Assign,
    Binary,
    Block,
    Expr,
    If,
    Literal,
    Print,
    Program,
    Stmt,
    Unary,
    VarDecl,
    VarRef,
    While,
)
from .errors import SemanticError


@dataclass
class Symbol:
    name: str


class ScopeStack:
    def __init__(self) -> None:
        self.scopes: List[Dict[str, Symbol]] = [{}]  # global

    def push(self) -> None:
        self.scopes.append({})

    def pop(self) -> None:
        if len(self.scopes) <= 1:
            raise RuntimeError("cannot pop global scope")
        self.scopes.pop()

    def declare(self, name: str, line: int, col: int) -> None:
        if name in self.scopes[-1]:
            raise SemanticError(f"Variable {name!r} redeclared at line {line}, col {col}")
        self.scopes[-1][name] = Symbol(name=name)

    def is_declared(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self.scopes))


class SemanticAnalyzer:
    """
    Semantic rules for MiniC:
    - variables must be declared before use
    - redeclaration in the same scope is not allowed
    - identifier names cannot start with '__' (reserved for temporaries in TAC)
    - only int expressions (comparisons/logicals produce int 0/1)
    """

    def __init__(self) -> None:
        self.sym = ScopeStack()

    def analyze(self, program: Program) -> None:
        for stmt in program.statements:
            self._stmt(stmt)

    def _stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            self._check_user_name(stmt.name, stmt.line, stmt.col)
            self.sym.declare(stmt.name, stmt.line, stmt.col)
            if stmt.init is not None:
                self._expr(stmt.init)
            return

        if isinstance(stmt, Assign):
            if not self.sym.is_declared(stmt.name):
                raise SemanticError(f"Assignment to undeclared variable {stmt.name!r} at line {stmt.line}, col {stmt.col}")
            self._expr(stmt.expr)
            return

        if isinstance(stmt, Print):
            self._expr(stmt.expr)
            return

        if isinstance(stmt, If):
            self._expr(stmt.cond)
            self.sym.push()
            for s in stmt.then_block.statements:
                self._stmt(s)
            self.sym.pop()
            if stmt.else_block is not None:
                self.sym.push()
                for s in stmt.else_block.statements:
                    self._stmt(s)
                self.sym.pop()
            return

        if isinstance(stmt, While):
            self._expr(stmt.cond)
            self.sym.push()
            for s in stmt.body.statements:
                self._stmt(s)
            self.sym.pop()
            return

        raise SemanticError(f"Unknown statement node {type(stmt)}")

    def _expr(self, expr: Expr) -> None:
        if isinstance(expr, Literal):
            return
        if isinstance(expr, VarRef):
            if not self.sym.is_declared(expr.name):
                raise SemanticError(f"Use of undeclared variable {expr.name!r} at line {expr.line}, col {expr.col}")
            self._check_user_name(expr.name, expr.line, expr.col)
            return
        if isinstance(expr, Unary):
            self._expr(expr.expr)
            return
        if isinstance(expr, Binary):
            self._expr(expr.left)
            self._expr(expr.right)
            return

        raise SemanticError(f"Unknown expression node {type(expr)}")

    def _check_user_name(self, name: str, line: int, col: int) -> None:
        if name.startswith("__"):
            raise SemanticError(f"Invalid identifier {name!r}: reserved prefix")

