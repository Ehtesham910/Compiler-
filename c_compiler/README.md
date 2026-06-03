# MiniC Compiler (Basic C Subset)

This is a **basic working compiler** for a small **C-like language** called **MiniC**.

It demonstrates the typical semester compiler pipeline:
1. Lexical analysis (lexer)
2. Syntax analysis (parser)
3. Semantic analysis (symbol table + errors)
4. Intermediate code generation (3-address code / TAC)
5. Back-end execution (TAC interpreter)
6. CLI runner + test cases

---

## MiniC Language

### Program
```
stmt*
```

### Statements
1. Declaration (int)
```
int x;
int x = 10;
```

2. Assignment
```
x = x + 1;
```

3. Print
```
print x;
```

4. If / Else
```
if (x < 10) { print x; } else { print 0; }
```

5. While
```
while (x < 10) { x = x + 1; }
```

### Expressions
Supported:
- Integers: `0`, `12`, `-3`
- Operators: `+ - * / %`
- Comparisons: `== != < <= > >=` (result is `1` or `0`)
- Logical: `&& || !` (result is `1` or `0`)
- Parentheses: `( ... )`

Notes:
- All values are treated as `int`.
- Division and modulo by zero produce a runtime error.

---

## Running

### CLI (compile and execute)
```powershell
python -m c_compiler.cli --file .\c_compiler\examples\sample1.cmini
```

### Compile only (and print TAC)
```powershell
python -m c_compiler.cli --file .\c_compiler\examples\sample1.cmini --no-run --print-tac
```

### How it works (pipeline)
For every source input the compiler runs these phases:
1. `lexer.py`: converts characters into tokens (with `line`/`col`)
2. `parser.py`: builds an AST (statements + expressions)
3. `semantic.py`: symbol table checks (declared before use, no redeclare in same scope)
4. `codegen.py`: AST -> TAC (3-address instructions using temporaries like `__t0`)
5. `interpreter.py`: executes TAC to produce output from `print`

---

## What gets generated (TAC)

TAC is a 3-address instruction list using temporaries like `__t0`, `__t1`, ...

Instructions:
- `LABEL name`
- `MOV dest, src`
- `UNOP dest = op arg` (op is `NOT` or `NEG`)
- `BINOP dest = a binop b` (binop is `ADD/SUB/.../EQ/.../AND/OR`)
- `JZ cond, label` (jump when cond is 0)
- `JMP label`
- `PRINT arg`

The interpreter executes the TAC directly and collects `print` output.

### Small TAC example
Source:
```
int x = 1 + 2 * 3;
print x;
```
TAC will look like:
```
__t0 = 2 MUL 3
x = 1 ADD __t0
PRINT x
```

---

## Semester-friendly implementation notes

### Semantic checks included
- Redeclaration in the same scope is an error
- Use of undeclared variable is an error
- Identifiers starting with `__` are rejected (reserved for compiler temporaries)

### Scope rules
- MiniC treats `{ ... }` blocks as new scopes:
  - `if {}` and `else {}` each get their own inner scope
  - `while {}` body gets its own inner scope

### Error message behavior
- Lexer errors show character position (`line`, `col`)
- Parser errors show token position
- Semantic errors show the identifier position for undeclared/redeclared variables

---

## Tests
Run:
```powershell
python -m c_compiler.tests.run_tests
```

