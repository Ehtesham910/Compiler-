from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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
from .tac import TacProgram


class TempFactory:
    def __init__(self) -> None:
        self.i = 0

    def new_temp(self) -> str:
        t = f"__t{self.i}"
        self.i += 1
        return t


class LabelFactory:
    def __init__(self) -> None:
        self.i = 0

    def new_label(self, prefix: str = "L") -> str:
        s = f"{prefix}{self.i}"
        self.i += 1
        return s


class CodeGenerator:
    def __init__(self) -> None:
        self.tfac = TempFactory()
        self.lfac = LabelFactory()
        self.instructions: List[Dict[str, Any]] = []

    def emit(self, ins: Dict[str, Any]) -> None:
        self.instructions.append(ins)

    def generate(self, program: Program) -> TacProgram:
        for stmt in program.statements:
            self._stmt(stmt)
        return TacProgram(instructions=self.instructions, entry_label=None)

    def _stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            if stmt.init is None:
                # Mini compiler: default init to 0 so runtime won't crash.
                self.emit({"op": "MOV", "dest": stmt.name, "src": 0})
            else:
                src = self._expr(stmt.init)
                self.emit({"op": "MOV", "dest": stmt.name, "src": src})
            return

        if isinstance(stmt, Assign):
            src = self._expr(stmt.expr)
            self.emit({"op": "MOV", "dest": stmt.name, "src": src})
            return

        if isinstance(stmt, Print):
            val = self._expr(stmt.expr)
            self.emit({"op": "PRINT", "arg": val})
            return

        if isinstance(stmt, If):
            else_label = self.lfac.new_label("ELSE_")
            end_label = self.lfac.new_label("ENDIF_")

            cond_val = self._expr(stmt.cond)
            self.emit({"op": "JZ", "cond": cond_val, "label": else_label})

            self._block(stmt.then_block)
            self.emit({"op": "JMP", "label": end_label})

            self.emit({"op": "LABEL", "name": else_label})
            if stmt.else_block is not None:
                self._block(stmt.else_block)

            self.emit({"op": "LABEL", "name": end_label})
            return

        if isinstance(stmt, While):
            start_label = self.lfac.new_label("WHILE_")
            end_label = self.lfac.new_label("ENDWHILE_")

            self.emit({"op": "LABEL", "name": start_label})
            cond_val = self._expr(stmt.cond)
            self.emit({"op": "JZ", "cond": cond_val, "label": end_label})
            self._block(stmt.body)
            self.emit({"op": "JMP", "label": start_label})
            self.emit({"op": "LABEL", "name": end_label})
            return

        raise RuntimeError(f"Unknown statement node {type(stmt)}")

    def _block(self, block: Block) -> None:
        for stmt in block.statements:
            self._stmt(stmt)

    def _expr(self, expr: Expr) -> Any:
        if isinstance(expr, Literal):
            return expr.value
        if isinstance(expr, VarRef):
            return expr.name
        if isinstance(expr, Unary):
            arg = self._expr(expr.expr)
            dest = self.tfac.new_temp()
            if expr.op == "!":
                self.emit({"op": "UNOP", "dest": dest, "op": "NOT", "arg": arg})
                return dest
            if expr.op == "-":
                self.emit({"op": "UNOP", "dest": dest, "op": "NEG", "arg": arg})
                return dest
            raise RuntimeError(f"Unknown unary operator {expr.op!r}")
        if isinstance(expr, Binary):
            a = self._expr(expr.left)
            b = self._expr(expr.right)
            dest = self.tfac.new_temp()
            op_map = {
                "+": "ADD",
                "-": "SUB",
                "*": "MUL",
                "/": "DIV",
                "%": "MOD",
                "==": "EQ",
                "!=": "NE",
                "<": "LT",
                "<=": "LE",
                ">": "GT",
                ">=": "GE",
                "&&": "AND",
                "||": "OR",
            }
            if expr.op not in op_map:
                raise RuntimeError(f"Unsupported binary operator {expr.op!r}")
            self.emit({"op": "BINOP", "dest": dest, "binop": op_map[expr.op], "a": a, "b": b})
            return dest

        raise RuntimeError(f"Unknown expression node {type(expr)}")


def generate_tac(program: Program) -> TacProgram:
    return CodeGenerator().generate(program)

