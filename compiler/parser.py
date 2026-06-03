from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .ast_nodes import (
    Assign,
    Binary,
    Block,
    Break,
    Case,
    Continue,
    Expr,
    For,
    If,
    Literal,
    Print,
    Program,
    Read,
    Stmt,
    Switch,
    Ternary,
    Unary,
    VarDecl,
    VarRef,
    While,
)
from .errors import ParseError
from .tokenizer import Token, lex


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

    def _expect(self, token_type: str, message: str) -> Token:
        t = self.state.peek()
        if t.type != token_type:
            raise ParseError(f"{message} at line {t.line}, col {t.col} (got {t.type})")
        return self.state.next()

    def parse(self) -> Program:
        statements: List[Stmt] = []
        while self.state.peek().type != "EOF":
            statements.append(self.parse_statement())
        return Program(statements=statements)

    def parse_statement(self) -> Stmt:
        t = self.state.peek()

        if t.type == "LET":
            self.state.next()
            ident = self._expect("IDENT", "Expected identifier after 'let'")
            expr: Expr
            if self.state.match("ASSIGN"):
                expr = self.parse_expression()
            else:
                expr = Literal(value=0.0)
            self._expect("SEMICOLON", "Expected ';' after variable declaration")
            return VarDecl(name=str(ident.value), expr=expr)

        if t.type == "PRINT":
            self.state.next()
            expr = self.parse_expression()
            self._expect("SEMICOLON", "Expected ';' after print statement")
            return Print(expr=expr)

        if t.type == "IF":
            self.state.next()
            self._expect("LPAREN", "Expected '(' after 'if'")
            cond = self.parse_expression()
            self._expect("RPAREN", "Expected ')' after if condition")
            then_block = self.parse_block()

            else_block: Optional[Block] = None
            if self.state.match("ELSE"):
                else_block = self.parse_block()

            return If(cond=cond, then_block=then_block, else_block=else_block)

        if t.type == "WHILE":
            self.state.next()
            self._expect("LPAREN", "Expected '(' after 'while'")
            cond = self.parse_expression()
            self._expect("RPAREN", "Expected ')' after while condition")
            body = self.parse_block()
            return While(cond=cond, body=body)

        if t.type == "FOR":
            self.state.next()
            self._expect("LPAREN", "Expected '(' after 'for'")
            init: Optional[Stmt] = None
            if not self.state.match("SEMICOLON"):
                # Parse init statement without requiring semicolon
                if self.state.peek().type == "LET":
                    self.state.next()
                    ident = self._expect("IDENT", "Expected identifier after 'let'")
                    expr: Expr
                    if self.state.match("ASSIGN"):
                        expr = self.parse_expression()
                    else:
                        expr = Literal(value=0.0)
                    init = VarDecl(name=str(ident.value), expr=expr)
                elif self.state.peek().type == "IDENT":
                    ident = self.state.next()
                    self._expect("ASSIGN", "Expected '=' in assignment")
                    expr = self.parse_expression()
                    init = Assign(name=str(ident.value), expr=expr)
                self._expect("SEMICOLON", "Expected ';' after init")
            cond: Optional[Expr] = None
            if not self.state.match("SEMICOLON"):
                cond = self.parse_expression()
                self._expect("SEMICOLON", "Expected ';' after condition")
            incr: Optional[Stmt] = None
            if not self.state.match("RPAREN"):
                if self.state.peek().type == "IDENT":
                    ident = self.state.next()
                    self._expect("ASSIGN", "Expected '=' in increment")
                    expr = self.parse_expression()
                    incr = Assign(name=str(ident.value), expr=expr)
                self._expect("RPAREN", "Expected ')' after increment")
            body = self.parse_block()
            return For(init=init, cond=cond, incr=incr, body=body)

        if t.type == "SWITCH":
            self.state.next()
            self._expect("LPAREN", "Expected '(' after 'switch'")
            expr = self.parse_expression()
            self._expect("RPAREN", "Expected ')' after switch expression")
            self._expect("LBRACE", "Expected '{' after switch")
            cases = []
            default: Optional[Block] = None
            while self.state.peek().type != "RBRACE":
                if self.state.match("CASE"):
                    value = self.parse_expression()
                    self._expect("COLON", "Expected ':' after case value")
                    body_stmts = []
                    while self.state.peek().type not in ["CASE", "DEFAULT", "RBRACE", "BREAK"]:
                        body_stmts.append(self.parse_statement())
                    cases.append(Case(value=value, body=Block(statements=body_stmts)))
                elif self.state.match("DEFAULT"):
                    self._expect("COLON", "Expected ':' after default")
                    body_stmts = []
                    while self.state.peek().type not in ["RBRACE", "BREAK"]:
                        body_stmts.append(self.parse_statement())
                    default = Block(statements=body_stmts)
                else:
                    raise ParseError(f"Expected 'case' or 'default' in switch at line {self.state.peek().line}")
            self._expect("RBRACE", "Expected '}' after switch")
            return Switch(expr=expr, cases=cases, default=default)

        if t.type == "BREAK":
            self.state.next()
            self._expect("SEMICOLON", "Expected ';' after break")
            return Break()

        if t.type == "CONTINUE":
            self.state.next()
            self._expect("SEMICOLON", "Expected ';' after continue")
            return Continue()

        # Assignment: IDENT '=' expr ';'
        if t.type == "IDENT":
            # Lookahead: IDENT ASSIGN ...
            if self.state.tokens[self.state.pos + 1].type != "ASSIGN":
                raise ParseError(f"Unexpected token after identifier at line {t.line}, col {t.col}")
            ident = self.state.next()
            self._expect("ASSIGN", "Expected '=' in assignment")
            expr = self.parse_expression()
            self._expect("SEMICOLON", "Expected ';' after assignment")
            return Assign(name=str(ident.value), expr=expr)

        raise ParseError(f"Unexpected token {t.type} at line {t.line}, col {t.col}")

    def parse_block(self) -> Block:
        self._expect("LBRACE", "Expected '{' to start block")
        statements: List[Stmt] = []
        while self.state.peek().type != "RBRACE":
            statements.append(self.parse_statement())
        self._expect("RBRACE", "Expected '}' to end block")
        return Block(statements=statements)

    # ---------- Expression parsing with precedence ----------

    def parse_expression(self) -> Expr:
        return self.parse_ternary()

    def parse_ternary(self) -> Expr:
        expr = self.parse_or()
        if self.state.match("QUESTION"):
            true_expr = self.parse_expression()
            self._expect("COLON", "Expected ':' in ternary expression")
            false_expr = self.parse_expression()
            return Ternary(cond=expr, true_expr=true_expr, false_expr=false_expr)
        return expr

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
            expr = self.parse_unary()
            return Unary(op="!", expr=expr)
        if self.state.match("MINUS"):
            expr = self.parse_unary()
            return Unary(op="-", expr=expr)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        t = self.state.peek()
        if t.type == "NUMBER":
            self.state.next()
            return Literal(value=t.value)

        if t.type == "STRING":
            self.state.next()
            return Literal(value=str(t.value))

        if t.type == "TRUE":
            self.state.next()
            return Literal(value=1)
        if t.type == "FALSE":
            self.state.next()
            return Literal(value=0)

        if t.type == "IDENT":
            self.state.next()
            return VarRef(name=str(t.value))

        if t.type == "READ":
            self.state.next()
            self._expect("LPAREN", "Expected '(' after 'read'")
            self._expect("RPAREN", "Expected ')' after 'read('")
            return Read()

        if t.type == "LPAREN":
            self.state.next()
            expr = self.parse_expression()
            self._expect("RPAREN", "Expected ')' after expression")
            return expr

        raise ParseError(f"Unexpected token {t.type} in expression at line {t.line}, col {t.col}")


def parse_source(source: str) -> Program:
    return Parser(source).parse()

