#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps


VERSION = "1.0.0"


# Braille dots layout:
#
#   1 4
#   2 5
#   3 6
#   7 8
#
# Each Braille character represents a 2 × 4 pixel block.

DOTS = (
    (0, 0, 0x01),  # dot 1
    (0, 1, 0x02),  # dot 2
    (0, 2, 0x04),  # dot 3
    (1, 0, 0x08),  # dot 4
    (1, 1, 0x10),  # dot 5
    (1, 2, 0x20),  # dot 6
    (0, 3, 0x40),  # dot 7
    (1, 3, 0x80),  # dot 8
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="image-to-braille.py",
        description="Convert an image to Unicode Braille art.",
        epilog="""\
Examples:
  python image-to-braille.py photo.jpg
  python image-to-braille.py photo.jpg --width 70
  python image-to-braille.py photo.jpg --width 70 --threshold 145
  python image-to-braille.py photo.jpg --output logo.txt
  python image-to-braille.py photo.jpg --width 70 --output logo.txt

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
        "image",
        type=Path,
        help="input image",
    )

    parser.add_argument(
        "--width",
        type=int,
        default=80,
        help="output width in Braille characters (default: 80)",
    )

    parser.add_argument(
        "--threshold",
        type=int,
        default=145,
        help="brightness threshold from 0 to 255 (default: 145)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="write output to a file instead of stdout",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.image.is_file():
        raise ValueError(f"image not found: {args.image}")

    if args.width < 1:
        raise ValueError("width must be greater than 0")

    if not 0 <= args.threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")


def load_image(path: Path) -> Image.Image:
    try:
        image = Image.open(path)
        image.load()
        return image
    except Exception as exc:
        raise ValueError(f"cannot open image: {exc}") from exc


def prepare_image(image: Image.Image) -> Image.Image:
    """Convert to grayscale and normalize contrast."""

    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)

    return image


def calculate_dimensions(
    image: Image.Image,
    width: int,
) -> tuple[int, int]:
    """
    Calculate pixel dimensions.

    A Braille cell is 2 pixels wide × 4 pixels high.

    Terminal characters are usually taller than they are wide,
    so we compensate vertically with a factor of 0.5.
    """

    pixel_width = width * 2

    aspect_ratio = image.height / image.width

    braille_rows = max(
        1,
        round(width * aspect_ratio * 0.5),
    )

    pixel_height = braille_rows * 4

    return pixel_width, pixel_height


def resize_image(
    image: Image.Image,
    width: int,
) -> Image.Image:
    pixel_width, pixel_height = calculate_dimensions(
        image,
        width,
    )

    return image.resize(
        (pixel_width, pixel_height),
        Image.Resampling.LANCZOS,
    )


def pixel_to_braille(
    image: Image.Image,
    threshold: int,
) -> str:
    """Convert a grayscale image into Unicode Braille."""

    pixels = image.load()
    width, height = image.size

    lines = []

    for y in range(0, height, 4):
        line = []

        for x in range(0, width, 2):
            value = 0

            for dx, dy, dot in DOTS:
                px = pixels[x + dx, y + dy]

                if px < threshold:
                    value |= dot

            line.append(chr(0x2800 + value))

        lines.append("".join(line).rstrip())

    # Remove empty rows at the top and bottom.
    while lines and not lines[0]:
        lines.pop(0)

    while lines and not lines[-1]:
        lines.pop()

    return "\n".join(lines)


def convert(
    image: Image.Image,
    width: int,
    threshold: int,
) -> str:
    """Convert an image to Braille art."""

    image = prepare_image(image)
    image = resize_image(image, width)

    return pixel_to_braille(
        image,
        threshold,
    )


def write_output(
    result: str,
    output: Path,
) -> None:
    """Write output, replacing any existing file."""

    output.write_text(
        result + ("\n" if result else ""),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()

    try:
        validate_args(args)
        image = load_image(args.image)

        result = convert(
            image,
            args.width,
            args.threshold,
        )

    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        try:
            write_output(result, args.output)
        except OSError as exc:
            print(
                f"Error: cannot write output: {exc}",
                file=sys.stderr,
            )
            return 1
    elif result:
        print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
