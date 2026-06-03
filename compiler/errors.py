class CompilerError(Exception):
    """Base error for the compiler pipeline."""


class LexError(CompilerError):
    """Raised when tokenization fails."""


class ParseError(CompilerError):
    """Raised when parsing fails."""


class SemanticError(CompilerError):
    """Raised when semantic checks fail."""


class RuntimeError(CompilerError):
    """Raised when VM execution fails."""

