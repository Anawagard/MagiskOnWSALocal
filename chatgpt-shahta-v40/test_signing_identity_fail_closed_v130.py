"""Source-only signing guard: never silently rotate the existing debug key.

This test inspects the manual-only workflow and never starts an Android build.
"""
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github/workflows/chatgpt-shahta-v40.yml"


def audit(source: str) -> None:
    assert "id: shahta-signing-cache" in source
    assert "actions/cache/restore@v4" in source
    assert "shahta-v44-debug-keystore-20261102" in source
    assert 'steps.shahta-signing-cache.outputs.cache-hit' in source
    assert '!= "true"' in source
    assert '[ ! -s "$HOME/.android/debug.keystore" ]' in source
    assert "exit 1" in source
    assert "keytool -genkeypair" not in source
    assert "keytool -list -v" in source
    assert 'test "$expected" = "$actual"' in source


def negative_cases(source: str) -> None:
    for changed in (
        source.replace('!= "true"', '== "true"', 1),
        source.replace("actions/cache/restore@v4", "actions/cache@v4", 1),
        source + "\n# keytool -genkeypair must never be invoked\n",
    ):
        try:
            audit(changed)
        except AssertionError:
            continue
        raise AssertionError("Unsafe signing regression was accepted")


if __name__ == "__main__":
    text = WORKFLOW.read_text(encoding="utf-8")
    audit(text)
    negative_cases(text)
    print("PASS: original debug identity required; no APK or Gradle executed")
