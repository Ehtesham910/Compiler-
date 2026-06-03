from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TacProgram:
    instructions: List[Dict[str, Any]]
    entry_label: Optional[str] = None

    def to_text(self) -> str:
        lines: List[str] = []
        for i, ins in enumerate(self.instructions):
            op = ins["op"]
            if op == "LABEL":
                lines.append(f"{ins['name']}:")
            elif op == "JMP":
                lines.append(f"{i}: JMP {ins['label']}")
            elif op == "JZ":
                lines.append(f"{i}: JZ {ins['cond']}, {ins['label']}")
            elif op == "PRINT":
                lines.append(f"{i}: PRINT {ins['arg']}")
            elif op in ("MOV",):
                lines.append(f"{i}: {ins['dest']} = {ins['src']}")
            elif op in ("UNOP",):
                lines.append(f"{i}: {ins['dest']} = {ins['op']} {ins['arg']}")
            elif op in ("BINOP",):
                lines.append(f"{i}: {ins['dest']} = {ins['a']} {ins['binop']} {ins['b']}")
            else:
                lines.append(f"{i}: {ins}")
        return "\n".join(lines)

