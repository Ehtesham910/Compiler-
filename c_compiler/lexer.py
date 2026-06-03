from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .errors import LexError


@dataclass(frozen=True)
class Token:
    type: str
    value: object
    line: int
    col: int


class Lexer:
    KEYWORDS = {
        "int": "INT",
        "if": "IF",
        "else": "ELSE",
        "while": "WHILE",
        "print": "PRINT",
        "true": "TRUE",
        "false": "FALSE",
    }

    _MULTI = {
        "==": "EQ",
        "!=": "NE",
        "<=": "LE",
        ">=": "GE",
        "&&": "AND",
        "||": "OR",
    }

    _SINGLE = {
        "+": "PLUS",
        "-": "MINUS",
        "*": "MUL",
        "/": "DIV",
        "%": "MOD",
        "<": "LT",
        ">": "GT",
        "!": "NOT",
        "=": "ASSIGN",
        ";": "SEMICOLON",
        "(": "LPAREN",
        ")": "RPAREN",
        "{": "LBRACE",
        "}": "RBRACE",
        ",": "COMMA",
    }

    _RE_NUMBER = re.compile(r"^(?:\d+(?:\.\d+)?|\.\d+)")
    _RE_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*")

    def __init__(self, source: str):
        self.source = source
        self.i = 0
        self.line = 1
        self.col = 1

    def _peek(self, n: int = 0) -> str:
        idx = self.i + n
        if idx >= len(self.source):
            return ""
        return self.source[idx]

    def _advance(self, n: int = 1) -> None:
        for _ in range(n):
            if self.i >= len(self.source):
                return
            ch = self.source[self.i]
            self.i += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.i < len(self.source):
            ch = self._peek()

            # whitespace
            if ch in " \t\r\n":
                self._advance()
                continue

            # line comment: //
            if ch == "/" and self._peek(1) == "/":
                while self.i < len(self.source) and self._peek() != "\n":
                    self._advance()
                continue

            # block comment: /* ... */
            if ch == "/" and self._peek(1) == "*":
                self._advance(2)
                while self.i < len(self.source):
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance(2)
                        break
                    self._advance()
                else:
                    raise LexError(f"Unterminated block comment at line {self.line}, col {self.col}")
                continue

            start_line, start_col = self.line, self.col

            two = self.source[self.i : self.i + 2]
            if two in self._MULTI:
                tokens.append(Token(self._MULTI[two], two, start_line, start_col))
                self._advance(2)
                continue

            if ch in self._SINGLE:
                tokens.append(Token(self._SINGLE[ch], ch, start_line, start_col))
                self._advance(1)
                continue

            # number: we treat numeric literals as integers (C-like int)
            m = self._RE_NUMBER.match(self.source[self.i :])
            if m:
                raw = m.group(0)
                self._advance(len(raw))
                if "." in raw:
                    # allow float in input, but cast to int (for this mini compiler)
                    tokens.append(Token("NUMBER", int(float(raw)), start_line, start_col))
                else:
                    tokens.append(Token("NUMBER", int(raw), start_line, start_col))
                continue

            # identifier / keyword
            m_ident = self._RE_IDENT.match(self.source[self.i :])
            if m_ident:
                raw = m_ident.group(0)
                self._advance(len(raw))
                ttype = self.KEYWORDS.get(raw, "IDENT")
                if ttype in ("TRUE", "FALSE"):
                    tokens.append(Token(ttype, 1 if raw == "true" else 0, start_line, start_col))
                else:
                    tokens.append(Token(ttype, raw, start_line, start_col))
                continue

            raise LexError(f"Unexpected character {ch!r} at line {self.line}, col {self.col}")

        tokens.append(Token("EOF", "", self.line, self.col))
        return tokens


def lex(source: str) -> List[Token]:
    return Lexer(source).tokenize()

