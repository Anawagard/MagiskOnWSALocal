"""Source-only guard for the SHA-256 certificate of the shipped v7.0.1 APK."""
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github/workflows/chatgpt-shahta-v40.yml"
CERT = "cba521972875548604af46ef77431e155f17fadd901c772c839b3889b81c83a0"
KEY_CHECK = 'if ! matches_original "$temporary_key"; then'
PUBLISH_KEY = 'mv -f "$temporary_key" "$original_key"'


def audit(source):
    lines = [line.strip() for line in source.splitlines()]
    for line in (
        "uses: actions/cache/restore@v4",
        "key: shahta-v44-debug-keystore-20261102",
        f"SHAHTA_CERT_SHA256: {CERT}",
        "SHAHTA_ORIGINAL_DEBUG_KEYSTORE_B64: ${{ secrets.SHAHTA_ORIGINAL_DEBUG_KEYSTORE_B64 }}",
        'if matches_original "$original_key"; then',
        KEY_CHECK,
        PUBLISH_KEY,
        'test "$actual" = "$SHAHTA_CERT_SHA256"',
    ):
        assert line in lines, line
    assert lines.index(KEY_CHECK) < lines.index(PUBLISH_KEY)
    assert "Entry type: PrivateKeyEntry" in source
    assert 'base64 --decode > "$temporary_key"' in source
    assert 'base64 --decode > "$original_key"' not in source
    assert "apksigner" in source and "certificate SHA-256 digest" in source
    assert "keytool -genkeypair" not in source


if __name__ == "__main__":
    text = WORKFLOW.read_text(encoding="utf-8")
    audit(text)
    for old, new in (
        (CERT, "0" * 64),
        ("secrets.SHAHTA_ORIGINAL_DEBUG_KEYSTORE_B64", "secrets.UNTRUSTED_KEY"),
        ("actions/cache/restore@v4", "actions/cache@v4"),
        (KEY_CHECK, f"# {KEY_CHECK}"),
        (PUBLISH_KEY, PUBLISH_KEY.replace("mv -f", "cp")),
    ):
        try:
            audit(text.replace(old, new, 1))
        except AssertionError:
            continue
        raise AssertionError(f"Unsafe signing regression was accepted: {old}")
    print("PASS: original certificate required for restored signing key and the APK")
