from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .ast import Assign, Binary, Block, Expr, If, Literal, Print, Program, Stmt, Unary, VarDecl, VarRef, While
from .errors import ParseError
from .lexer import Token, lex


@dataclass
class ParseState:
    tokens: List[Token]
    pos: int = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def next(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def match(self, token_type: str) -> bool:
        if self.peek().type == token_type:
            self.pos += 1
            return True
        return False


class Parser:
    def __init__(self, source: str):
        self.state = ParseState(tokens=lex(source))

    def _expect(self, token_type: str, msg: str) -> Token:
        t = self.state.peek()
        if t.type != token_type:
            raise ParseError(f"{msg} at line {t.line}, col {t.col} (got {t.type})")
        return self.state.next()

    def parse(self) -> Program:
        stmts: List[Stmt] = []
        while self.state.peek().type != "EOF":
            stmts.append(self.parse_stmt())
        return Program(statements=stmts)

    def parse_block(self) -> Block:
        self._expect("LBRACE", "Expected '{'")
        stmts: List[Stmt] = []
        while self.state.peek().type != "RBRACE":
            stmts.append(self.parse_stmt())
        self._expect("RBRACE", "Expected '}'")
        return Block(statements=stmts)

    def parse_stmt(self) -> Stmt:
        t = self.state.peek()

        if t.type == "INT":
            self.state.next()
            ident = self._expect("IDENT", "Expected variable name after 'int'")
            init: Optional[Expr] = None
            if self.state.match("ASSIGN"):
                init = self.parse_expression()
            self._expect("SEMICOLON", "Expected ';' after declaration")
            return VarDecl(name=str(ident.value), init=init, line=ident.line, col=ident.col)

        if t.type == "IDENT":
            # IDENT '=' expr ';'
            ident = self.state.next()
            self._expect("ASSIGN", "Expected '=' after identifier")
            expr = self.parse_expression()
            self._expect("SEMICOLON", "Expected ';' after assignment")
            return Assign(name=str(ident.value), expr=expr, line=ident.line, col=ident.col)

        if t.type == "PRINT":
            self.state.next()
            expr = self.parse_expression()
            self._expect("SEMICOLON", "Expected ';' after print")
            # line/col for error pointing: keyword token
            return Print(expr=expr, line=t.line, col=t.col)

        if t.type == "IF":
            self.state.next()
            self._expect("LPAREN", "Expected '(' after 'if'")
            cond = self.parse_expression()
            self._expect("RPAREN", "Expected ')' after condition")
            then_block = self.parse_block()
            else_block: Optional[Block] = None
            if self.state.match("ELSE"):
                else_block = self.parse_block()
            return If(cond=cond, then_block=then_block, else_block=else_block, line=t.line, col=t.col)

        if t.type == "WHILE":
            self.state.next()
            self._expect("LPAREN", "Expected '(' after 'while'")
            cond = self.parse_expression()
            self._expect("RPAREN", "Expected ')' after condition")
            body = self.parse_block()
            return While(cond=cond, body=body, line=t.line, col=t.col)

        raise ParseError(f"Unexpected token {t.type} at line {t.line}, col {t.col}")

    # ---------- Expression parsing ----------
    def parse_expression(self) -> Expr:
        return self.parse_or()

    def parse_or(self) -> Expr:
        expr = self.parse_and()
        while self.state.match("OR"):
            right = self.parse_and()
            expr = Binary(op="||", left=expr, right=right)
        return expr

    def parse_and(self) -> Expr:
        expr = self.parse_equality()
        while self.state.match("AND"):
            right = self.parse_equality()
            expr = Binary(op="&&", left=expr, right=right)
        return expr

    def parse_equality(self) -> Expr:
        expr = self.parse_relational()
        while True:
            if self.state.match("EQ"):
                right = self.parse_relational()
                expr = Binary(op="==", left=expr, right=right)
                continue
            if self.state.match("NE"):
                right = self.parse_relational()
                expr = Binary(op="!=", left=expr, right=right)
                continue
            return expr

    def parse_relational(self) -> Expr:
        expr = self.parse_add()
        while True:
            if self.state.match("LT"):
                right = self.parse_add()
                expr = Binary(op="<", left=expr, right=right)
                continue
            if self.state.match("LE"):
                right = self.parse_add()
                expr = Binary(op="<=", left=expr, right=right)
                continue
            if self.state.match("GT"):
                right = self.parse_add()
                expr = Binary(op=">", left=expr, right=right)
                continue
            if self.state.match("GE"):
                right = self.parse_add()
                expr = Binary(op=">=", left=expr, right=right)
                continue
            return expr

    def parse_add(self) -> Expr:
        expr = self.parse_mul()
        while True:
            if self.state.match("PLUS"):
                right = self.parse_mul()
                expr = Binary(op="+", left=expr, right=right)
                continue
            if self.state.match("MINUS"):
                right = self.parse_mul()
                expr = Binary(op="-", left=expr, right=right)
                continue
            return expr

    def parse_mul(self) -> Expr:
        expr = self.parse_unary()
        while True:
            if self.state.match("MUL"):
                right = self.parse_unary()
                expr = Binary(op="*", left=expr, right=right)
                continue
            if self.state.match("DIV"):
                right = self.parse_unary()
                expr = Binary(op="/", left=expr, right=right)
                continue
            if self.state.match("MOD"):
                right = self.parse_unary()
                expr = Binary(op="%", left=expr, right=right)
                continue
            return expr

    def parse_unary(self) -> Expr:
        if self.state.match("NOT"):
            return Unary(op="!", expr=self.parse_unary())
        if self.state.match("MINUS"):
            return Unary(op="-", expr=self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        t = self.state.peek()

        if t.type == "NUMBER":
            self.state.next()
            return Literal(value=int(t.value))

        if t.type == "TRUE":
            self.state.next()
            return Literal(value=1)

        if t.type == "FALSE":
            self.state.next()
            return Literal(value=0)

        if t.type == "IDENT":
            self.state.next()
            return VarRef(name=str(t.value), line=t.line, col=t.col)

        if t.type == "LPAREN":
            self.state.next()
            expr = self.parse_expression()
            self._expect("RPAREN", "Expected ')'")
            return expr

        raise ParseError(f"Unexpected token {t.type} in expression at line {t.line}, col {t.col}")


def parse_source(source: str) -> Program:
    return Parser(source).parse()

