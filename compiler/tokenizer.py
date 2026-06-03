from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .errors import LexError


@dataclass(frozen=True)
class Token:
    type: str
    value: object
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token(type={self.type!r}, value={self.value!r}, line={self.line}, col={self.col})"


class Lexer:
    """
    Tokenizes MiniLang source code.

    Supported:
    - keywords: let, print, if, else, while, true, false
    - numbers: int/float
    - identifiers
    - operators: + - * / == != < <= > >= && || ! = ;
    - punctuation: ( ) { }
    - comments: // until end of line
    """

    KEYWORDS = {
        "let": "LET",
        "print": "PRINT",
        "if": "IF",
        "else": "ELSE",
        "while": "WHILE",
        "true": "TRUE",
        "false": "FALSE",
        "switch": "SWITCH",
        "case": "CASE",
        "default": "DEFAULT",
        "break": "BREAK",
        "continue": "CONTINUE",
        "for": "FOR",
        "read": "READ",
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
        "?": "QUESTION",
        "<": "LT",
        ">": "GT",
        "!": "NOT",
        "=": "ASSIGN",
        ";": "SEMICOLON",
        ":": "COLON",
        "(": "LPAREN",
        ")": "RPAREN",
        "{": "LBRACE",
        "}": "RBRACE",
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

            # Whitespace
            if ch in " \t\r\n":
                self._advance()
                continue

            # Line comments: //
            if ch == "/" and self._peek(1) == "/":
                while self.i < len(self.source) and self._peek() != "\n":
                    self._advance()
                continue

            start_line, start_col = self.line, self.col

            # String literals
            if ch == '"':
                self._advance(1)  # skip opening "
                start = self.i
                while self.i < len(self.source) and self._peek() != '"':
                    self._advance(1)
                if self.i >= len(self.source):
                    raise LexError(f"Unterminated string at line {start_line}, col {start_col}")
                value = self.source[start : self.i]
                self._advance(1)  # skip closing "
                tokens.append(Token("STRING", value, start_line, start_col))
                continue

            # Multi-char operators
            two = self.source[self.i : self.i + 2]
            if two in self._MULTI:
                tokens.append(Token(self._MULTI[two], two, start_line, start_col))
                self._advance(2)
                continue

            # Single-char operators / punctuation
            if ch in self._SINGLE:
                tokens.append(Token(self._SINGLE[ch], ch, start_line, start_col))
                self._advance(1)
                continue

            # Number
            m_num = self._RE_NUMBER.match(self.source[self.i :])
            if m_num:
                raw = m_num.group(0)
                self._advance(len(raw))
                if "." in raw:
                    val: object = float(raw)
                else:
                    val = int(raw)
                tokens.append(Token("NUMBER", val, start_line, start_col))
                continue

            # Identifier / keyword
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

