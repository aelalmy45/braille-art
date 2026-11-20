"""Tests for --color (ANSI 24-bit output)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from braille_art import image_to_braille


ANSI_FG = re.compile(r"\x1b\[38;2;(\d+);(\d+);(\d+)m")
RESET = "\x1b[0m"


def red_image(width: int = 4, height: int = 8) -> Image.Image:
    return Image.new("RGB", (width, height), (255, 0, 0))


def split_image(width: int = 4, height: int = 8) -> Image.Image:
    """Left half dark red, right half bright white."""
    image = Image.new("RGB", (width, height), (255, 255, 255))
    for x in range(width // 2):
        for y in range(height):
            image.putpixel((x, y), (128, 0, 0))
    return image


class TestColorOutput:
    def test_dots_carry_source_color(self):
        result = image_to_braille.convert(red_image(), 2, 145, color=True)
        assert "\x1b[38;2;255;0;0m" in result
        assert "⣿" in result

    def test_lines_end_with_reset(self):
        result = image_to_braille.convert(red_image(), 2, 145, color=True)
        for line in result.split("\n"):
            assert line.endswith(RESET)

    def test_blank_cells_have_no_color(self):
        # right half is bright: no dots, so no escape codes for those cells
        result = image_to_braille.convert(split_image(), 2, 145, color=True)
        line = result.split("\n")[0]
        assert line.count("\x1b[") == 2  # one color + one reset per line

    def test_color_matches_dark_half(self):
        # autocontrast stretches (128, 0, 0) red channel: 128 -> 255 in gray,
        # but the color comes from the original pixels, not the grayscale ones
        result = image_to_braille.convert(split_image(), 2, 145, color=True)
        match = ANSI_FG.search(result)
        assert match is not None
        r, g, b = (int(group) for group in match.groups())
        assert r > g and r > b

    def test_no_color_without_flag(self):
        result = image_to_braille.convert(red_image(), 2, 145)
        assert "\x1b[" not in result

    def test_repeated_color_emits_one_code(self):
        # two adjacent cells with the same color share one escape code
        result = image_to_braille.convert(red_image(), 2, 145, color=True)
        line = result.split("\n")[0]
        assert len(ANSI_FG.findall(line)) == 1

    def test_color_with_invert(self):
        # inverted, the bright half draws the dots and carries white
        result = image_to_braille.convert(split_image(), 2, 145, invert=True, color=True)
        match = ANSI_FG.search(result)
        assert match is not None
        r, g, b = (int(group) for group in match.groups())
        assert r == 255 and g == 255 and b == 255

    def test_color_with_dither(self):
        result = image_to_braille.convert(red_image(), 2, dither=True, color=True)
        assert ANSI_FG.search(result) is not None

    def test_grayscale_source_gets_gray_color(self):
        image = Image.new("L", (4, 8), 0)
        result = image_to_braille.convert(image, 2, 145, color=True)
        match = ANSI_FG.search(result)
        assert match is not None
        r, g, b = (int(group) for group in match.groups())
        assert r == g == b


class TestCli:
    def test_color_flag(self, tmp_path, capsys):
        path = tmp_path / "img.png"
        red_image(20, 20).save(path)
        sys.argv = ["braille-art", str(path), "--width", "10", "--color"]
        assert image_to_braille.main() == 0
        assert "\x1b[38;2;" in capsys.readouterr().out

    def test_color_output_file_keeps_escape_codes(self, tmp_path):
        path = tmp_path / "img.png"
        red_image(20, 20).save(path)
        out = tmp_path / "out.txt"
        sys.argv = ["braille-art", str(path), "--width", "10", "--color", "-o", str(out)]
        assert image_to_braille.main() == 0
        assert "\x1b[38;2;" in out.read_text(encoding="utf-8")
