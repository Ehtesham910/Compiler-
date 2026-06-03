from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .codegen import generate_tac
from .errors import LexError, ParseError, RuntimeError, SemanticError, MiniCError
from .interpreter import TACInterpreter, ExecResult
from .parser import parse_source
from .semantic import SemanticAnalyzer


@dataclass
class CompileRunResult:
    ok: bool
    output_text: str
    error_text: str
    tac_text: str


def compile_and_run(source: str, *, run: bool = True, print_tac: bool = False) -> CompileRunResult:
    try:
        program = parse_source(source)
        SemanticAnalyzer().analyze(program)
        tac = generate_tac(program)
        tac_text = tac.to_text()

        if not run:
            return CompileRunResult(ok=True, output_text="", error_text="", tac_text=tac_text)

        result = TACInterpreter().execute(tac)
        return CompileRunResult(ok=True, output_text=result.output_text, error_text="", tac_text=tac_text)
    except (MiniCError,) as e:
        return CompileRunResult(ok=False, output_text="", error_text=str(e), tac_text="")


def compile_only(source: str) -> CompileRunResult:
    return compile_and_run(source, run=False)

