from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .ast_nodes import Program
from .codegen import generate_bytecode
from .errors import CompilerError, LexError, ParseError, RuntimeError, SemanticError
from .parser import parse_source
from .semantic import SemanticAnalyzer
from .vm import VM


@dataclass
class CompileResult:
    ok: bool
    output_text: str
    error_text: str
    bytecode: list[dict[str, Any]]
    source_hash: str


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compile_source(source: str) -> CompileResult:
    source_hash = _sha256(source)
    try:
        program: Program = parse_source(source)
        SemanticAnalyzer().analyze(program)
        bytecode_obj = generate_bytecode(program)
        return CompileResult(
            ok=True,
            output_text="",
            error_text="",
            bytecode=bytecode_obj.to_jsonable(),
            source_hash=source_hash,
        )
    except (CompilerError,) as e:
        return CompileResult(
            ok=False,
            output_text="",
            error_text=str(e),
            bytecode=[],
            source_hash=source_hash,
        )


def compile_and_run(source: str, run: bool = True) -> CompileResult:
    res = compile_source(source)
    if not res.ok or not run:
        return res

    try:
        vm = VM()
        vm_result = vm.execute(res.bytecode)
        return CompileResult(
            ok=True,
            output_text=vm_result.output_text,
            error_text="",
            bytecode=res.bytecode,
            source_hash=res.source_hash,
        )
    except RuntimeError as e:
        return CompileResult(
            ok=False,
            output_text="",
            error_text=str(e),
            bytecode=res.bytecode,
            source_hash=res.source_hash,
        )

