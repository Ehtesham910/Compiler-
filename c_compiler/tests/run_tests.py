from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from c_compiler.compiler import compile_and_run


@dataclass
class TestCase:
    name: str
    path: Path
    should_fail: bool = False
    expected_output: str = ""


def run_case(tc: TestCase) -> None:
    source = tc.path.read_text(encoding="utf-8")
    res = compile_and_run(source, run=True)

    if tc.should_fail:
        if res.ok:
            raise AssertionError(f"{tc.name}: expected failure but got ok")
        return

    if not res.ok:
        raise AssertionError(f"{tc.name}: expected ok but got error: {res.error_text}")

    got = res.output_text.strip()
    exp = tc.expected_output.strip()
    if got != exp:
        raise AssertionError(f"{tc.name}: output mismatch.\nExpected: {exp!r}\nGot: {got!r}")


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    tests = [
        TestCase(
            name="sample1",
            path=base / "examples" / "sample1.cmini",
            expected_output="5",
        ),
        TestCase(
            name="sample2",
            path=base / "examples" / "sample2.cmini",
            expected_output="16",
        ),
        TestCase(
            name="semantic_error",
            path=base / "examples" / "semantic_error.cmini",
            should_fail=True,
        ),
    ]

    for tc in tests:
        run_case(tc)

    print("All tests passed")


if __name__ == "__main__":
    main()

