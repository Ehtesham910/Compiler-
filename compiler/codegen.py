from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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
from .bytecode import Bytecode


@dataclass
class Label:
    id: int


class CodeGenerator:
    def __init__(self) -> None:
        self.instructions: List[Dict[str, Any]] = []
        self.labels_to_pos: Dict[int, int] = {}
        self.unresolved_jumps: List[Tuple[int, int]] = []
        self._next_label_id = 0
        self.loop_stack: List[Tuple[Label, Label]] = []  # (continue_label, break_label)

    def emit(self, op: str, arg: Any = None) -> int:
        idx = len(self.instructions)
        ins = {"op": op}
        if arg is not None:
            ins["arg"] = arg
        self.instructions.append(ins)
        return idx

    def new_label(self) -> Label:
        lid = self._next_label_id
        self._next_label_id += 1
        return Label(id=lid)

    def mark_label(self, label: Label) -> None:
        self.labels_to_pos[label.id] = len(self.instructions)

    def emit_jmp_label(self, op: str, label: Label) -> None:
        # Store a placeholder, patch later.
        jump_ins_idx = self.emit(op, arg=label.id)
        self.unresolved_jumps.append((jump_ins_idx, label.id))

    def patch_labels(self) -> None:
        for ins_idx, label_id in self.unresolved_jumps:
            target = self.labels_to_pos.get(label_id)
            if target is None:
                raise RuntimeError(f"Unknown label id {label_id}")
            self.instructions[ins_idx]["arg"] = target

    def generate(self, program: Program) -> Bytecode:
        for stmt in program.statements:
            self._gen_stmt(stmt)
        self.emit("HALT")
        self.patch_labels()
        return Bytecode(instructions=self.instructions)

    # ---------- Statements ----------

    def _gen_block(self, block: Block) -> None:
        for stmt in block.statements:
            self._gen_stmt(stmt)

    def _gen_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            self._gen_expr(stmt.expr)
            self.emit("STORE", arg=stmt.name)
            return

        if isinstance(stmt, Assign):
            self._gen_expr(stmt.expr)
            self.emit("STORE", arg=stmt.name)
            return

        if isinstance(stmt, Print):
            self._gen_expr(stmt.expr)
            self.emit("PRINT")
            return

        if isinstance(stmt, If):
            end_label = self.new_label()
            else_label = self.new_label()

            self._gen_expr(stmt.cond)
            # Jump to else if cond is false (0)
            self.emit_jmp_label("JZ", else_label)
            self._gen_block(stmt.then_block)
            self.emit_jmp_label("JMP", end_label)

            self.mark_label(else_label)
            if stmt.else_block is not None:
                self._gen_block(stmt.else_block)

            self.mark_label(end_label)
            return

        if isinstance(stmt, While):
            start_label = self.new_label()
            end_label = self.new_label()

            self.mark_label(start_label)
            self._gen_expr(stmt.cond)
            self.emit_jmp_label("JZ", end_label)
            self.loop_stack.append((start_label, end_label))
            self._gen_block(stmt.body)
            self.loop_stack.pop()
            self.emit_jmp_label("JMP", start_label)
            self.mark_label(end_label)
            return

        if isinstance(stmt, For):
            start_label = self.new_label()
            end_label = self.new_label()

            if stmt.init:
                self._gen_stmt(stmt.init)
            self.mark_label(start_label)
            if stmt.cond:
                self._gen_expr(stmt.cond)
                self.emit_jmp_label("JZ", end_label)
            self.loop_stack.append((start_label, end_label))
            self._gen_block(stmt.body)
            self.loop_stack.pop()
            if stmt.incr:
                self._gen_stmt(stmt.incr)
            self.emit_jmp_label("JMP", start_label)
            self.mark_label(end_label)
            return

        if isinstance(stmt, Switch):
            end_label = self.new_label()
            self._gen_expr(stmt.expr)
            case_end_labels = []
            for case in stmt.cases:
                case_label = self.new_label()
                case_end_labels.append(case_label)
                self.emit("DUP")
                self._gen_expr(case.value)
                self.emit("CMPEQ")
                self.emit_jmp_label("JZ", case_label)
                self.loop_stack.append((None, end_label))
                self._gen_block(case.body)
                self.loop_stack.pop()
                self.emit_jmp_label("JMP", end_label)
                self.mark_label(case_label)
            if stmt.default:
                self.loop_stack.append((None, end_label))
                self._gen_block(stmt.default)
                self.loop_stack.pop()
            self.mark_label(end_label)
            self.emit("POP")
            return

        if isinstance(stmt, Break):
            if not self.loop_stack:
                raise RuntimeError("Break outside of loop or switch")
            self.emit_jmp_label("JMP", self.loop_stack[-1][1])
            return

        if isinstance(stmt, Continue):
            if not self.loop_stack or self.loop_stack[-1][0] is None:
                raise RuntimeError("Continue outside of loop")
            self.emit_jmp_label("JMP", self.loop_stack[-1][0])
            return

        raise RuntimeError(f"Unknown statement node {type(stmt)}")

    # ---------- Expressions ----------

    def _gen_expr(self, expr: Expr) -> None:
        if isinstance(expr, Literal):
            self.emit("CONST", arg=expr.value)
            return

        if isinstance(expr, VarRef):
            self.emit("LOAD", arg=expr.name)
            return

        if isinstance(expr, Unary):
            self._gen_expr(expr.expr)
            if expr.op == "!":
                self.emit("NOT")
            elif expr.op == "-":
                self.emit("NEG")
            else:
                raise RuntimeError(f"Unknown unary operator {expr.op!r}")
            return

        if isinstance(expr, Binary):
            self._gen_expr(expr.left)
            self._gen_expr(expr.right)
            op = expr.op
            arith = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD"}
            if op in arith:
                self.emit(arith[op])
                return

            comps = {
                "==": "CMPEQ",
                "!=": "CMPNE",
                "<": "CMPLT",
                "<=": "CMPLE",
                ">": "CMPGT",
                ">=": "CMPGE",
            }
            if op in comps:
                self.emit(comps[op])
                return

            logic = {"&&": "AND", "||": "OR"}
            if op in logic:
                self.emit(logic[op])
                return

            raise RuntimeError(f"Unknown binary operator {op!r}")

        if isinstance(expr, Ternary):
            end_label = self.new_label()
            else_label = self.new_label()

            self._gen_expr(expr.cond)
            self.emit_jmp_label("JZ", else_label)
            self._gen_expr(expr.true_expr)
            self.emit_jmp_label("JMP", end_label)

            self.mark_label(else_label)
            self._gen_expr(expr.false_expr)

            self.mark_label(end_label)
            return

        if isinstance(expr, Read):
            self.emit("INPUT")
            return

        raise RuntimeError(f"Unknown expression node {type(expr)}")


def generate_bytecode(program: Program) -> Bytecode:
    return CodeGenerator().generate(program)

