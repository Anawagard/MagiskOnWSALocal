"""Source-only signing guard: never silently rotate the existing debug key.

This test inspects the manual-only workflow and never starts an Android build.
"""
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github/workflows/chatgpt-shahta-v40.yml"


def audit(source: str) -> None:
    assert "id: shahta-signing-cache" in source
    assert "actions/cache/restore@v4" in source
    assert "shahta-v44-debug-keystore-20261102" in source
    assert "SHAHTA_ORIGINAL_DEBUG_KEYSTORE_B64" in source
    assert "secrets.SHAHTA_ORIGINAL_DEBUG_KEYSTORE_B64" in source
    assert "base64 --decode" in source
    assert 'temporary_key="$(mktemp "$HOME/.android/.shahta-key.XXXXXXXX")"' in source
    assert "trap 'rm -f \"$temporary_key\"' EXIT" in source
    assert 'base64 --decode > "$temporary_key"' in source
    assert 'test -s "$temporary_key"' in source
    assert 'keytool -list -keystore "$temporary_key" -alias androiddebugkey -storepass android >/dev/null' in source
    assert 'mv -f "$temporary_key" "$HOME/.android/debug.keystore"' in source
    assert source.index('keytool -list -keystore "$temporary_key"') < source.index('mv -f "$temporary_key"')
    assert 'base64 --decode > "$HOME/.android/debug.keystore"' not in source
    assert '[ ! -s "$HOME/.android/debug.keystore" ]' in source
    assert "exit 1" in source
    assert "keytool -genkeypair" not in source
    assert "keytool -list -v" in source
    assert 'test "$expected" = "$actual"' in source


def negative_cases(source: str) -> None:
    for changed in (
        source.replace("secrets.SHAHTA_ORIGINAL_DEBUG_KEYSTORE_B64", "secrets.UNTRUSTED_KEY", 1),
        source.replace("actions/cache/restore@v4", "actions/cache@v4", 1),
        source.replace('mv -f "$temporary_key" "$HOME/.android/debug.keystore"', 'cp "$temporary_key" "$HOME/.android/debug.keystore"', 1),
        source.replace('keytool -list -keystore "$temporary_key"', 'true # keytool -list -keystore "$temporary_key"', 1),
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
    print("PASS: original debug identity restored only from cache or protected secret; no APK or Gradle executed")
