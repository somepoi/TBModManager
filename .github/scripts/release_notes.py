"""Extract the latest stable version's changelog for a tagged release."""

import argparse
from pathlib import Path
import re


VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"


def extract_notes(changelog: str, tag: str) -> str:
    tag_match = re.fullmatch(rf"v?({VERSION})", tag)
    if not tag_match:
        raise ValueError("Release tag must use X.Y.Z or vX.Y.Z without leading zeros.")
    version = tag_match.group(1)
    found = False
    notes = []
    fence = None

    for line in changelog.splitlines():
        if fence is not None:
            if re.fullmatch(rf" {{0,3}}{re.escape(fence[0])}{{{fence[1]},}}[ \t]*", line):
                fence = None
        else:
            fence_match = re.match(r" {0,3}(`{3,}|~{3,})", line)
            if fence_match:
                marker = fence_match.group(1)
                fence = (marker[0], len(marker))
            elif not found:
                heading = re.fullmatch(rf"#[ \t]+({VERSION})[ \t]*", line)
                if heading:
                    if heading.group(1) != version:
                        raise ValueError(
                            f"The latest changelog version is {heading.group(1)}, "
                            f"but the release tag is {tag}."
                        )
                    found = True
                    continue
            elif re.match(r"#[ \t]+", line):
                break
        if found:
            notes.append(line)

    if not found:
        raise ValueError("CHANGELOG.md has no version section headed '# X.Y.Z'.")
    body = "\n".join(notes).strip()
    if not body:
        raise ValueError(f"Changelog notes for {version} are empty.")
    return body + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("changelog", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        notes = extract_notes(args.changelog.read_text(encoding="utf-8-sig"), args.tag)
        args.output.write_text(notes, encoding="utf-8")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
