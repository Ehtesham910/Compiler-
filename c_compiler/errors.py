class MiniCError(Exception):
    """Base error for lexer/parser/semantic/codegen/runtime."""


class LexError(MiniCError):
    pass


class ParseError(MiniCError):
    pass


class SemanticError(MiniCError):
    pass


class RuntimeError(MiniCError):
    pass

