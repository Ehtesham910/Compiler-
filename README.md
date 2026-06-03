# Python Mini-Compiler (6th Semester Project)

This project implements a **working compiler** in Python for a small statement language, including:

- Lexer (tokenizer)
- Parser (recursive descent)
- Semantic analysis (scopes + variable checks)
- Code generation to a simple **stack-based bytecode**
- A **virtual machine (VM)** that executes the bytecode
- A **CLI** to compile/run
- A **Flask REST backend** + **SQLite** to store run history
- A minimal **web UI** to submit code and view output

---

## 1) Language (MiniLang) Specification

### Program

A program is a sequence of statements.

### Statements

1. Variable declaration:

```txt
let x = 10;
let y;  // declares y with default value 0
```

2. Assignment:

```txt
x = x + 1;
```

3. Print:

```txt
print x;
```

4. If / Else:

```txt
if (x < 10) {
  print x;
} else {
  print 999;
}
```

5. While:

```txt
while (x < 10) {
  x = x + 1;
}
```

6. For:

```txt
for (let i = 0; i < 10; i = i + 1) {
  print i;
}
```

7. Switch:

```txt
switch (x) {
  case 1:
    print "one";
  case 2:
    print "two";
  default:
    print "other";
}
```

Note: Each case has an implicit break; explicit break statements are not supported in switch.

8. Break / Continue:

```txt
while (true) {
  if (x > 10) break;
  x = x + 1;
  if (x % 2 == 0) continue;
  print x;
}
```

### Expressions

Supported operators (with usual precedence):

- Arithmetic: `+  -  *  /  %`
- Comparisons: `==  !=  <  <=  >  >=`
- Logical: `&&  ||  !`
- Parentheses: `( ... )`

Literals:

- Numbers: `123` or `3.14`
- Booleans: `true`, `false`
- Strings: `"hello world"`

New features:

- Ternary: `condition ? true_val : false_val`
- Input: `read()` (reads a value from user stdin)

Notes:

- Semicolons are required for statements.
- Conditions use boolean results of comparison/logical expressions; any non-zero value is treated as true by the VM.

---

## 2) Project Structure

- `compiler/` - compiler core (lexer/parser/semantic/codegen/VM)
- `cli/` - command-line compiler runner
- `backend/` - Flask API + SQLite storage
- `frontend/` - minimal web UI (static files)
- `examples/` - sample MiniLang programs

---

## 3) How to Run (Backend + Web UI)

### 3.1 Setup Python environment

From the project root (`.../Compiler`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3.2 Start the backend (Flask)

```powershell
python backend\app.py
```

Backend runs at:

- `http://127.0.0.1:5000`

### 3.3 Use the web UI

Open:

- `http://127.0.0.1:5000/`

Paste MiniLang code and click **Compile & Run**.

---

## 4) How to Run (CLI)

### Compile + run from a file

```powershell
python cli\main.py --file .\examples\sample1.lang
```

### Compile only (no execution)

```powershell
python cli\main.py --file .\examples\sample1.lang --no-run
```

### Run with source passed directly

```powershell
python cli\main.py --source "let x=3; print x; x=x+4; print x;"
```

---

## 5) SQLite Database (Implementation Details)

The backend stores run history in:

- `backend/compiler.db` (auto-created)

Schema:

- `runs(id, created_at, source_hash, source_text, ok, output_text, error_text, bytecode_json)`

This allows you to show compilation results later (for a report).

---

## 5.1) Backend REST API (Implementation Details)

### Endpoint

`POST /api/compile`

### Request JSON

```json
{
  "source": "MiniLang code as a string",
  "run": true
}
```

### Response JSON (success)

```json
{
  "ok": true,
  "run_id": 1,
  "output": "printed output",
  "bytecode": [{ "op": "CONST", "arg": 1 }]
}
```

### Response JSON (error)

```json
{
  "ok": false,
  "run_id": 1,
  "error": "semantic/parse/runtime error message",
  "bytecode": []
}
```

The backend always inserts a row into SQLite (even on failure) so you can demonstrate error handling in the project.

---

## 6) Compiler Creating Guide (Report-Friendly)

### Step 1: Lexical Analysis (Lexer)

- Convert the raw source string into tokens like:
  - identifiers (`IDENT`)
  - numbers (`NUMBER`)
  - keywords (`let`, `print`, `if`, `else`, `while`, `true`, `false`)
  - operators (`+ - * / == != < <= ... && || !`)
  - punctuation (`; ( ) { }`)

### Step 2: Syntax Analysis (Parser)

- Use a recursive descent parser with precedence climbing:
  - OR (`||`)
  - AND (`&&`)
  - Equality (`== !=`)
  - Relational (`< <= > >=`)
  - Additive (`+ -`)
  - Multiplicative (`* /`)
  - Unary (`!` and unary `-`)
  - Primary (`NUMBER`, identifiers, parentheses)

### Step 3: Semantic Analysis

- Build scopes using a symbol table stack.
- Checks performed:
  - Using variables before declaration => semantic error
  - Redeclaring the same variable in the same scope => semantic error
  - Conditions/expressions are always type-compatible in this mini-language (VM uses numeric truthiness)

### Step 4: Code Generation

- Generate a **stack-based bytecode**:
  - expressions push results onto the stack
  - statements emit stack operations and jumps for control flow

Key bytecode instructions:

- `CONST` (push constant)
- `LOAD` / `STORE` (variable access)
- arithmetic ops: `ADD SUB MUL DIV`
- comparison ops: `CMPEQ CMPNE CMPLT CMPLE CMPGT CMPGE`
- logical ops: `AND OR NOT`
- control flow: `JZ` (jump if zero) / `JMP`
- `PRINT`

VM behavior conventions:

- `JZ` pops the condition value; if it is “falsey” (0.0), execution jumps.
- Comparisons push `1` (true) or `0` (false).
- `&&` / `||` are implemented as non-short-circuit boolean ops in this project.

### Step 5: Virtual Machine (Execution)

- VM executes bytecode sequentially.
- For jumps it uses an instruction pointer.
- For `PRINT`, it appends output to a list and returns it at the end.

---

## 7) Example Programs

Check:

- `examples/sample1.lang`
- `examples/sample2.lang`

---

## 8) Extending the Compiler (If You Need Extra Features)

Suggested enhancements for a semester report:

- Add short-circuit evaluation for `&&` / `||`
- Add `break` / `continue` in `while`
- Add function definitions/calls
- Add better error messages with token excerpts
- Add compiler optimization (constant folding)
