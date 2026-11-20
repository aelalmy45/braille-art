#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

from braille_art import __version__


VERSION = __version__

# Threshold used internally when dithering reduces the image to 1 bit.
DITHER_THRESHOLD = 128


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
        description="Convert an image to Unicode Braille art.",
        epilog="""\
Examples:
  braille-art photo.jpg
  braille-art photo.jpg --width 70
  braille-art photo.jpg --width 70 --threshold 145
  braille-art photo.jpg --invert
  braille-art photo.jpg --color
  braille-art photo.jpg --dither
  braille-art photo.jpg --width 70 --dither --output logo.txt

Without --threshold, the threshold is detected automatically
with Otsu's method. The --output file is overwritten on every run.
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
        default=None,
        help="brightness threshold from 0 to 255 "
        "(default: detected automatically with Otsu's method, "
        "ignored with --dither)",
    )

    parser.add_argument(
        "--invert",
        action="store_true",
        help="draw dots for bright pixels instead of dark ones "
        "(try it when the result looks swapped on a dark terminal)",
    )

    parser.add_argument(
        "--color",
        action="store_true",
        help="render the art in ANSI 24-bit color, averaging the source "
        "pixels under each dot (best viewed in a terminal; escape codes "
        "are kept when writing to a file)",
    )

    parser.add_argument(
        "--dither",
        action="store_true",
        help="use Floyd-Steinberg dithering instead of a flat threshold "
        "(usually much better for photos)",
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

    if args.threshold is not None and not 0 <= args.threshold <= 255:
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


def apply_dithering(image: Image.Image) -> Image.Image:
    """
    Reduce to a 1-bit image with Floyd-Steinberg dithering.

    Dithering spreads quantization error across neighboring pixels,
    which preserves shading and detail that a flat threshold loses.
    The result is a bilevel image whose pixels are 0 or 255.
    """

    return image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)


def otsu_threshold(image: Image.Image) -> int:
    """
    Pick a brightness threshold automatically with Otsu's method.

    Otsu's method looks at the brightness histogram and chooses the
    threshold that best separates dark pixels from bright ones, so
    most images work well without hand-tuning --threshold.
    """

    histogram = image.histogram()
    total = image.width * image.height

    sum_all = sum(value * count for value, count in enumerate(histogram))

    sum_dark = 0.0
    weight_dark = 0
    best_variance = -1.0
    best = 128

    for value, count in enumerate(histogram):
        weight_dark += count

        if weight_dark == 0:
            continue

        weight_bright = total - weight_dark

        if weight_bright == 0:
            break

        sum_dark += value * count

        mean_dark = sum_dark / weight_dark
        mean_bright = (sum_all - sum_dark) / weight_bright

        variance = weight_dark * weight_bright * (mean_dark - mean_bright) ** 2

        if variance > best_variance:
            best_variance = variance
            best = value

    # Otsu splits the histogram into pixels <= best (dark) and the
    # rest (bright). pixel_to_braille draws a dot when px < threshold,
    # so shift the split point up by one to keep the darkest class.
    return min(best + 1, 255)


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
    invert: bool = False,
    color_image: Image.Image | None = None,
) -> str:
    """
    Convert a grayscale image into Unicode Braille.

    With color_image (an RGB image of the same pixel size), each drawn
    cell is wrapped in an ANSI 24-bit escape carrying the average color
    of the source pixels under its dots.
    """

    pixels = image.load()
    color_pixels = color_image.load() if color_image is not None else None
    width, height = image.size

    lines = []

    for y in range(0, height, 4):
        line = []
        last_color = None
        colored = False

        for x in range(0, width, 2):
            value = 0

            for dx, dy, dot in DOTS:
                px = pixels[x + dx, y + dy]

                on = px < threshold

                if invert:
                    on = not on

                if on:
                    value |= dot

            char = chr(0x2800 + value)

            if color_pixels is not None and value:
                red = green = blue = count = 0

                for dx, dy, dot in DOTS:
                    if value & dot:
                        r, g, b = color_pixels[x + dx, y + dy][:3]
                        red += r
                        green += g
                        blue += b
                        count += 1

                color = (red // count, green // count, blue // count)

                if color != last_color:
                    line.append(f"\x1b[38;2;{color[0]};{color[1]};{color[2]}m")
                    last_color = color

                colored = True

            line.append(char)

        text = "".join(line).rstrip()

        if colored:
            text += "\x1b[0m"

        lines.append(text)

    # Remove empty rows at the top and bottom.
    while lines and not lines[0]:
        lines.pop(0)

    while lines and not lines[-1]:
        lines.pop()

    return "\n".join(lines)


def convert(
    image: Image.Image,
    width: int,
    threshold: int | None = None,
    dither: bool = False,
    invert: bool = False,
    color: bool = False,
) -> str:
    """Convert an image to Braille art."""

    color_image = image.convert("RGB") if color else None

    image = prepare_image(image)
    image = resize_image(image, width)

    if color_image is not None:
        color_image = color_image.resize(
            image.size,
            Image.Resampling.LANCZOS,
        )

    if dither:
        image = apply_dithering(image)
        threshold = DITHER_THRESHOLD
    elif threshold is None:
        threshold = otsu_threshold(image)

    return pixel_to_braille(
        image,
        threshold,
        invert,
        color_image,
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
            args.dither,
            args.invert,
            args.color,
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
