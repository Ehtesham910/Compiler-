from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .errors import RuntimeError


def _is_truthy(x: Any) -> bool:
    try:
        return float(x) != 0.0
    except Exception:
        return bool(x)


@dataclass
class VMResult:
    output_lines: List[str]

    @property
    def output_text(self) -> str:
        return "\n".join(self.output_lines)


class VM:
    def __init__(self) -> None:
        self.stack: List[Any] = []
        self.vars: Dict[str, Any] = {}
        self.ip: int = 0
        self.output_lines: List[str] = []

    def _pop(self) -> Any:
        if not self.stack:
            raise RuntimeError("VM stack underflow")
        return self.stack.pop()

    def execute(self, instructions: List[Dict[str, Any]]) -> VMResult:
        self.stack = []
        self.vars = {}
        self.ip = 0
        self.output_lines = []

        while self.ip < len(instructions):
            ins = instructions[self.ip]
            self.ip += 1
            op = ins["op"]
            arg = ins.get("arg")

            if op == "CONST":
                self.stack.append(arg)
                continue

            if op == "LOAD":
                if arg not in self.vars:
                    raise RuntimeError(f"Runtime: undefined variable {arg!r}")
                self.stack.append(self.vars[arg])
                continue

            if op == "STORE":
                val = self._pop()
                self.vars[arg] = val
                continue

            if op == "DUP":
                if not self.stack:
                    raise RuntimeError("VM stack underflow")
                self.stack.append(self.stack[-1])
                continue

            if op == "POP":
                self._pop()
                continue

            if op == "INPUT":
                s = input().strip()  # Read from console
                try:
                    if "." in s:
                        val = float(s)
                    else:
                        val = float(int(s))  # Ensure it's numeric
                except ValueError:
                    # Keep as string if not numeric
                    val = s
                self.stack.append(val)
                continue

            # Arithmetic
            if op in ("ADD", "SUB", "MUL", "DIV", "MOD"):
                b = self._pop()
                a = self._pop()
                if op == "ADD":
                    self.stack.append(a + b)
                elif op == "SUB":
                    self.stack.append(a - b)
                elif op == "MUL":
                    self.stack.append(a * b)
                elif op == "DIV":
                    if float(b) == 0.0:
                        raise RuntimeError("Runtime: division by zero")
                    self.stack.append(a / b)
                else:  # MOD
                    if float(b) == 0.0:
                        raise RuntimeError("Runtime: modulo by zero")
                    self.stack.append(a % b)
                continue

            # Comparisons -> push 1/0
            if op in ("CMPEQ", "CMPNE", "CMPLT", "CMPLE", "CMPGT", "CMPGE"):
                b = self._pop()
                a = self._pop()
                if op == "CMPEQ":
                    res = float(a) == float(b)
                elif op == "CMPNE":
                    res = float(a) != float(b)
                elif op == "CMPLT":
                    res = float(a) < float(b)
                elif op == "CMPLE":
                    res = float(a) <= float(b)
                elif op == "CMPGT":
                    res = float(a) > float(b)
                else:  # CMPGE
                    res = float(a) >= float(b)
                self.stack.append(1 if res else 0)
                continue

            # Logical ops (non-short-circuit)
            if op in ("AND", "OR"):
                b = self._pop()
                a = self._pop()
                av = _is_truthy(a)
                bv = _is_truthy(b)
                if op == "AND":
                    self.stack.append(1 if (av and bv) else 0)
                else:
                    self.stack.append(1 if (av or bv) else 0)
                continue

            if op == "NOT":
                a = self._pop()
                self.stack.append(1 if not _is_truthy(a) else 0)
                continue

            if op == "NEG":
                a = self._pop()
                self.stack.append(-a)
                continue

            # Control flow
            if op == "JZ":
                cond = self._pop()
                if not _is_truthy(cond):
                    self.ip = int(arg)
                continue

            if op == "JMP":
                self.ip = int(arg)
                continue

            if op == "PRINT":
                val = self._pop()
                self.output_lines.append(str(val))
                continue

            if op == "HALT":
                break

            raise RuntimeError(f"Runtime: unknown instruction op {op!r}")

        return VMResult(output_lines=self.output_lines)

