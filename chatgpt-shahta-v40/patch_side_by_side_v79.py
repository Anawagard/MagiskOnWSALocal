"""Prepare a disposable v7.9.0 project for an independent Android install.

Apply after the standard redesign patches. Build the resulting unsigned
debug APK and sign it with the dedicated side-by-side keystore.
"""
from argparse import ArgumentParser
from pathlib import Path


def apply(project: Path) -> None:
    gradle = project / "app/build.gradle"
    manifest = project / "app/src/main/AndroidManifest.xml"
    build = gradle.read_text(encoding="utf-8")
    app = manifest.read_text(encoding="utf-8")
    if "versionName '7.9.0'" not in build:
        raise ValueError("Expected the prepared v7.9.0 Android project")
    changes = (
        ("applicationId 'com.bezdna.mine'", "applicationId 'com.bezdna.mine.redesign'"),
        ("signingConfig signingConfigs.shahtaDebug", "signingConfig null"),
    )
    for old, new in changes:
        if build.count(old) != 1:
            raise ValueError(f"Missing or ambiguous Gradle anchor: {old}")
        build = build.replace(old, new, 1)
    original_label = 'android:label="Шахта без дна"'
    if app.count(original_label) != 1:
        raise ValueError("Missing or ambiguous original app label")
    app = app.replace(original_label, 'android:label="Шахта без дна — редизайн"', 1)

    # The Java namespace and JSON save format are shared with the standard APK.
    gradle.write_text(build, encoding="utf-8")
    manifest.write_text(app, encoding="utf-8")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    apply(parser.parse_args().project)
