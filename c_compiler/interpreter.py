from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .errors import RuntimeError
from .tac import TacProgram


def _to_int_c(x: Any) -> int:
    # Interpreter is C-like for ints: everything is int, division truncates toward zero.
    try:
        return int(x)
    except Exception:
        return 0


def _truthy_int(x: Any) -> bool:
    return _to_int_c(x) != 0


@dataclass
class ExecResult:
    output_lines: List[str]

    @property
    def output_text(self) -> str:
        return "\n".join(self.output_lines)


class TACInterpreter:
    def execute(self, tac: TacProgram) -> ExecResult:
        labels: Dict[str, int] = {}
        for idx, ins in enumerate(tac.instructions):
            if ins["op"] == "LABEL":
                labels[ins["name"]] = idx

        mem: Dict[str, Any] = {}
        output: List[str] = []

        ip = 0
        while ip < len(tac.instructions):
            ins = tac.instructions[ip]
            ip += 1

            op = ins["op"]

            if op == "LABEL":
                continue

            if op == "MOV":
                dest = ins["dest"]
                src = ins["src"]
                mem[dest] = mem[src] if isinstance(src, str) else _to_int_c(src)
                continue

            if op == "UNOP":
                dest = ins["dest"]
                arg = ins["arg"]
                aval = mem[arg] if isinstance(arg, str) else _to_int_c(arg)
                uop = ins["op"]
                if uop == "NOT":
                    mem[dest] = 1 if not _truthy_int(aval) else 0
                elif uop == "NEG":
                    mem[dest] = -_to_int_c(aval)
                else:
                    raise RuntimeError(f"Unknown unary op {uop!r}")
                continue

            if op == "BINOP":
                dest = ins["dest"]
                a = ins["a"]
                b = ins["b"]
                aval = mem[a] if isinstance(a, str) else _to_int_c(a)
                bval = mem[b] if isinstance(b, str) else _to_int_c(b)
                binop = ins["binop"]

                if binop == "ADD":
                    mem[dest] = aval + bval
                elif binop == "SUB":
                    mem[dest] = aval - bval
                elif binop == "MUL":
                    mem[dest] = aval * bval
                elif binop == "DIV":
                    if bval == 0:
                        raise RuntimeError("division by zero")
                    mem[dest] = int(aval / bval)  # trunc toward zero
                elif binop == "MOD":
                    if bval == 0:
                        raise RuntimeError("mod by zero")
                    mem[dest] = int(aval % bval)
                elif binop == "EQ":
                    mem[dest] = 1 if aval == bval else 0
                elif binop == "NE":
                    mem[dest] = 1 if aval != bval else 0
                elif binop == "LT":
                    mem[dest] = 1 if aval < bval else 0
                elif binop == "LE":
                    mem[dest] = 1 if aval <= bval else 0
                elif binop == "GT":
                    mem[dest] = 1 if aval > bval else 0
                elif binop == "GE":
                    mem[dest] = 1 if aval >= bval else 0
                elif binop == "AND":
                    mem[dest] = 1 if (_truthy_int(aval) and _truthy_int(bval)) else 0
                elif binop == "OR":
                    mem[dest] = 1 if (_truthy_int(aval) or _truthy_int(bval)) else 0
                else:
                    raise RuntimeError(f"Unknown binary op {binop!r}")

                continue

            if op == "JMP":
                label = ins["label"]
                ip = labels[label]
                continue

            if op == "JZ":
                cond = ins["cond"]
                cval = mem[cond] if isinstance(cond, str) else _to_int_c(cond)
                label = ins["label"]
                if not _truthy_int(cval):
                    ip = labels[label]
                continue

            if op == "PRINT":
                arg = ins["arg"]
                val = mem[arg] if isinstance(arg, str) else _to_int_c(arg)
                output.append(str(val))
                continue

            raise RuntimeError(f"Unknown instruction op {op!r}")

        return ExecResult(output_lines=output)

