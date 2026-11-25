"""Adversarial source-only regression tests for release patch ordering.

Does not run Android, Gradle, patches, or GitHub Actions.
"""
from audit_release_patch_order_v93 import MODERN, TESTS, audit

NAMES = set(MODERN + TESTS)
def workflow(commands):
    return "on:\n  workflow_dispatch:\nsteps:\n" + "".join(
        f"      python3 chatgpt-shahta-v40/{name}\n" for name in commands
    )

def check(commands, should_pass, label):
    _, problems = audit(workflow(commands), NAMES)
    assert (not problems) == should_pass, (label, problems)

def main():
    valid = MODERN + TESTS
    check(valid, True, "valid sequence")
    check(valid[:-1], False, "missing last test")
    check(valid + [MODERN[0]], False, "duplicate patch")
    check(valid + [TESTS[0]], False, "duplicate test")
    check(MODERN[::-1] + TESTS, False, "reversed patch order")
    check(MODERN + TESTS[::-1], False, "reversed test order")
    check(TESTS + MODERN, False, "tests before patches")
    check(MODERN[:-1] + [TESTS[0], MODERN[-1]] + TESTS[1:],
          False, "test interleaved with patches")
    check([name for name in valid if name != MODERN[4]],
          False, "missing middle patch")
    check(valid + ["unexpected.py", "unexpected.py"], False,
          "duplicate unexpected command")
    print("PASS: 10 adversarial release-order scenarios (source-only)")

if __name__ == "__main__":
    main()
