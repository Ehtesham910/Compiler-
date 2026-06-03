from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Bytecode:
    instructions: List[Dict[str, Any]]

    def to_jsonable(self) -> List[Dict[str, Any]]:
        return self.instructions

