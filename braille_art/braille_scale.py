#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from braille_art import __version__


VERSION = __version__

BRAILLE_BASE = 0x2800


# Braille:
#
#   1 4
#   2 5
#   3 6
#   7 8

DOTS = (
    (0, 0, 0x01),
    (0, 1, 0x02),
    (0, 2, 0x04),
    (0, 3, 0x40),
    (1, 0, 0x08),
    (1, 1, 0x10),
    (1, 2, 0x20),
    (1, 3, 0x80),
)


def is_braille(ch: str) -> bool:
    return 0x2800 <= ord(ch) <= 0x28FF


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resize Unicode Braille art.",
        epilog="""\
Examples:
  braille-scale logo.txt
  braille-scale logo.txt 0.75
  braille-scale logo.txt 0.50
  braille-scale logo.txt 0.50 --output small-logo.txt

The --output file is overwritten on every run.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    parser.add_argument(
        "file",
        type=Path,
        help="input Braille art file",
    )

    parser.add_argument(
        "scale",
        type=float,
        nargs="?",
        default=0.75,
        help="scale factor from 0 to 1 (default: 0.75)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="write output to a file instead of stdout",
    )

    return parser.parse_args()


def decode(lines: list[str]) -> list[list[bool]]:
    """Decode Braille text into a 2×4 bitmap."""

    width = max(len(line) for line in lines)

    bitmap = [[False] * (width * 2) for _ in range(len(lines) * 4)]

    for cy, line in enumerate(lines):
        for cx, ch in enumerate(line):
            if not is_braille(ch):
                continue

            mask = ord(ch) - BRAILLE_BASE

            for dx, dy, bit in DOTS:
                if mask & bit:
                    bitmap[cy * 4 + dy][cx * 2 + dx] = True

    return bitmap


def crop(bitmap: list[list[bool]]) -> list[list[bool]]:
    """Remove empty borders."""

    if not bitmap:
        return bitmap

    height = len(bitmap)
    width = len(bitmap[0])

    min_x = width
    max_x = -1
    min_y = height
    max_y = -1

    for y in range(height):
        for x in range(width):
            if bitmap[y][x]:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if max_x == -1:
        return bitmap

    return [row[min_x : max_x + 1] for row in bitmap[min_y : max_y + 1]]


def resize(
    bitmap: list[list[bool]],
    scale: float,
) -> list[list[bool]]:
    """
    Resize bitmap using area averaging.

    Braille requires a 2×4 cell structure, so the
    resulting dimensions are adjusted accordingly.
    """

    old_h = len(bitmap)
    old_w = len(bitmap[0])

    new_w = max(2, round(old_w * scale))
    new_h = max(4, round(old_h * scale))

    # Braille requires 2×4 cells.
    new_w -= new_w % 2
    new_h -= new_h % 4

    new_w = max(2, new_w)
    new_h = max(4, new_h)

    result = [[False] * new_w for _ in range(new_h)]

    sx = old_w / new_w
    sy = old_h / new_h

    for ny in range(new_h):
        y0 = ny * sy
        y1 = (ny + 1) * sy

        y_start = int(y0)
        y_end = min(
            old_h,
            max(y_start + 1, int(y1)),
        )

        for nx in range(new_w):
            x0 = nx * sx
            x1 = (nx + 1) * sx

            x_start = int(x0)
            x_end = min(
                old_w,
                max(x_start + 1, int(x1)),
            )

            filled = 0.0
            area = 0.0

            for y in range(y_start, y_end):
                wy = min(y1, y + 1) - max(y0, y)

                if wy <= 0:
                    continue

                for x in range(x_start, x_end):
                    wx = min(x1, x + 1) - max(x0, x)

                    if wx <= 0:
                        continue

                    weight = wx * wy
                    area += weight

                    if bitmap[y][x]:
                        filled += weight

            if area:
                result[ny][nx] = filled / area >= 0.30

    return result


def encode(bitmap: list[list[bool]]) -> list[str]:
    """Encode a 2×4 bitmap as Unicode Braille."""

    height = len(bitmap)
    width = len(bitmap[0])

    result = []

    for y in range(0, height, 4):
        line = []

        for x in range(0, width, 2):
            mask = 0

            for dx, dy, bit in DOTS:
                px = x + dx
                py = y + dy

                if py < height and px < width and bitmap[py][px]:
                    mask |= bit

            line.append(chr(BRAILLE_BASE + mask))

        result.append("".join(line).rstrip("\u2800"))

    return result


def scale_braille(
    lines: list[str],
    scale: float,
) -> list[str]:
    """Scale Braille art."""

    bitmap = decode(lines)
    bitmap = crop(bitmap)

    if not bitmap:
        return []

    bitmap = resize(
        bitmap,
        scale,
    )

    return encode(bitmap)


def read_braille_file(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read input: {exc}") from exc

    lines = [line for line in lines if any(is_braille(ch) for ch in line)]

    if not lines:
        raise ValueError("no Braille characters found")

    return lines


def write_output(
    result: list[str],
    output: Path,
) -> None:
    """Write output, replacing any existing file."""

    text = "\n".join(result)

    output.write_text(
        text + ("\n" if text else ""),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()

    if not args.file.is_file():
        print(
            f"Error: file not found: {args.file}",
            file=sys.stderr,
        )
        return 1

    if not 0 < args.scale <= 1:
        print(
            "Error: scale must be greater than 0 and less than or equal to 1",
            file=sys.stderr,
        )
        return 1

    try:
        lines = read_braille_file(args.file)

        result = scale_braille(
            lines,
            args.scale,
        )

    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        try:
            write_output(
                result,
                args.output,
            )
        except OSError as exc:
            print(
                f"Error: cannot write output: {exc}",
                file=sys.stderr,
            )
            return 1
    else:
        print("\n".join(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
