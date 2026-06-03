from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .ast_nodes import (
    Assign,
    Binary,
    Block,
    Break,
    Case,
    Continue,
    Expr,
    For,
    If,
    Literal,
    Print,
    Program,
    Read,
    Stmt,
    Switch,
    Ternary,
    Unary,
    VarDecl,
    VarRef,
    While,
)
from .errors import SemanticError


@dataclass
class Symbol:
    name: str


class SymbolTable:
    def __init__(self) -> None:
        self.scopes: List[Dict[str, Symbol]] = [{}]

    def push(self) -> None:
        self.scopes.append({})

    def pop(self) -> None:
        if len(self.scopes) <= 1:
            raise RuntimeError("cannot pop global scope")
        self.scopes.pop()

    def declare(self, name: str) -> None:
        current = self.scopes[-1]
        if name in current:
            raise SemanticError(f"Variable {name!r} redeclared in the same scope")
        current[name] = Symbol(name=name)

    def is_declared(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self.scopes))


class SemanticAnalyzer:
    """
    Semantic checks for MiniLang:
    - variables must be declared before use
    - redeclaration in the same scope is not allowed
    - expression trees are traversed to ensure all VarRefs are valid
    """

    def __init__(self) -> None:
        self.sym = SymbolTable()

    def analyze(self, program: Program) -> None:
        for stmt in program.statements:
            self._analyze_stmt(stmt)

    def _analyze_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            self._analyze_expr(stmt.expr)
            self.sym.declare(stmt.name)
            return

        if isinstance(stmt, Assign):
            if not self.sym.is_declared(stmt.name):
                raise SemanticError(f"Assignment to undeclared variable {stmt.name!r}")
            self._analyze_expr(stmt.expr)
            return

        if isinstance(stmt, Print):
            self._analyze_expr(stmt.expr)
            return

        if isinstance(stmt, If):
            self._analyze_expr(stmt.cond)
            # If/else blocks get their own scopes.
            self.sym.push()
            for s in stmt.then_block.statements:
                self._analyze_stmt(s)
            self.sym.pop()
            if stmt.else_block is not None:
                self.sym.push()
                for s in stmt.else_block.statements:
                    self._analyze_stmt(s)
                self.sym.pop()
            return

        if isinstance(stmt, While):
            self._analyze_expr(stmt.cond)
            self.sym.push()
            for s in stmt.body.statements:
                self._analyze_stmt(s)
            self.sym.pop()
            return

        if isinstance(stmt, For):
            self.sym.push()
            if stmt.init:
                self._analyze_stmt(stmt.init)
            if stmt.cond:
                self._analyze_expr(stmt.cond)
            if stmt.incr:
                self._analyze_stmt(stmt.incr)
            for s in stmt.body.statements:
                self._analyze_stmt(s)
            self.sym.pop()
            return

        if isinstance(stmt, Switch):
            self._analyze_expr(stmt.expr)
            for case in stmt.cases:
                self._analyze_expr(case.value)
                self.sym.push()
                for s in case.body.statements:
                    self._analyze_stmt(s)
                self.sym.pop()
            if stmt.default:
                self.sym.push()
                for s in stmt.default.statements:
                    self._analyze_stmt(s)
                self.sym.pop()
            return

        if isinstance(stmt, Break):
            return

        if isinstance(stmt, Continue):
            return

        raise SemanticError(f"Unknown statement type: {type(stmt)}")

    def _analyze_expr(self, expr: Expr) -> None:
        if isinstance(expr, Literal):
            return

        if isinstance(expr, VarRef):
            if not self.sym.is_declared(expr.name):
                raise SemanticError(f"Use of undeclared variable {expr.name!r}")
            return

        if isinstance(expr, Unary):
            self._analyze_expr(expr.expr)
            return

        if isinstance(expr, Binary):
            self._analyze_expr(expr.left)
            self._analyze_expr(expr.right)
            return

        if isinstance(expr, Ternary):
            self._analyze_expr(expr.cond)
            self._analyze_expr(expr.true_expr)
            self._analyze_expr(expr.false_expr)
            return

        if isinstance(expr, Read):
            return

        raise SemanticError(f"Unknown expression type: {type(expr)}")

