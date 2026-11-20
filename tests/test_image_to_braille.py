"""Tests for braille_art.image_to_braille."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from braille_art import image_to_braille


THRESHOLD = 145  # the fixed default these known-output tests pin down


def solid_image(width: int, height: int, value: int) -> Image.Image:
    return Image.new("L", (width, height), value)


def half_image(width: int, height: int) -> Image.Image:
    """Left half black (0), right half white (255)."""
    image = Image.new("L", (width, height), 255)
    for x in range(width // 2):
        for y in range(height):
            image.putpixel((x, y), 0)
    return image


class TestDimensions:
    def test_pixel_size_from_width(self):
        image = solid_image(200, 100, 0)
        assert image_to_braille.calculate_dimensions(image, 40) == (80, 40)

    def test_minimum_one_row(self):
        image = solid_image(1000, 10, 0)
        _w, h = image_to_braille.calculate_dimensions(image, 10)
        assert h == 4


class TestKnownOutputs:
    """Images sized so the internal resize is the identity mapping."""

    def test_black_image_is_all_dots(self):
        image = solid_image(4, 8, 0)
        result = image_to_braille.convert(image, 2, THRESHOLD)
        assert result == "⣿⣿\n⣿⣿"

    def test_white_image_is_all_blank_cells(self):
        image = solid_image(4, 8, 255)
        result = image_to_braille.convert(image, 2, THRESHOLD)
        assert result == "\u2800\u2800\n\u2800\u2800"

    def test_half_black_image(self):
        image = half_image(4, 8)
        result = image_to_braille.convert(image, 2, THRESHOLD)
        assert result == "⣿\u2800\n⣿\u2800"

    def test_single_dark_pixel_sets_one_dot(self):
        image = solid_image(4, 8, 255)
        image.putpixel((0, 0), 0)  # dot 1 of the first cell
        result = image_to_braille.convert(image, 2, THRESHOLD)
        assert result == "⠁\u2800\n\u2800\u2800"

    def test_threshold_boundary(self):
        # pixel just below the threshold draws a dot, just above does not
        below = solid_image(2, 4, THRESHOLD - 1)
        above = solid_image(2, 4, THRESHOLD)
        assert image_to_braille.convert(below, 1, THRESHOLD) == "⣿"
        assert image_to_braille.convert(above, 1, THRESHOLD) == "\u2800"

    def test_color_image_input(self):
        image = Image.new("RGB", (4, 8), (0, 0, 0))
        result = image_to_braille.convert(image, 2, THRESHOLD)
        assert result == "⣿⣿\n⣿⣿"


class TestDithering:
    def gradient(self, width: int = 16, height: int = 16) -> Image.Image:
        image = Image.new("L", (width, height))
        for y in range(height):
            for x in range(width):
                image.putpixel((x, y), round(255 * x / (width - 1)))
        return image

    def test_deterministic(self):
        first = image_to_braille.convert(self.gradient(), 8, THRESHOLD, dither=True)
        second = image_to_braille.convert(self.gradient(), 8, THRESHOLD, dither=True)
        assert first == second

    def test_gradient_produces_mixed_output(self):
        result = image_to_braille.convert(self.gradient(), 8, THRESHOLD, dither=True)
        assert "⣿" in result  # dark end fully filled
        assert result.strip("⣿\n")  # and lighter cells elsewhere

    def test_dither_ignores_threshold(self):
        low = image_to_braille.convert(self.gradient(), 8, 10, dither=True)
        high = image_to_braille.convert(self.gradient(), 8, 250, dither=True)
        assert low == high

    def test_black_and_white_extremes(self):
        black = image_to_braille.convert(solid_image(4, 8, 0), 2, THRESHOLD, dither=True)
        white = image_to_braille.convert(solid_image(4, 8, 255), 2, THRESHOLD, dither=True)
        assert black == "⣿⣿\n⣿⣿"
        assert white == "\u2800\u2800\n\u2800\u2800"


class TestCli:
    def make_image(self, tmp_path: Path, name: str = "img.png") -> Path:
        path = tmp_path / name
        half_image(20, 20).save(path)
        return path

    def run_cli(self, *argv: str) -> int:
        sys.argv = ["braille-art", *argv]
        return image_to_braille.main()

    def test_stdout(self, tmp_path, capsys):
        path = self.make_image(tmp_path)
        assert self.run_cli(str(path), "--width", "10") == 0
        out = capsys.readouterr().out
        assert "⣿" in out

    def test_output_file(self, tmp_path):
        path = self.make_image(tmp_path)
        out = tmp_path / "out.txt"
        assert self.run_cli(str(path), "--width", "10", "-o", str(out)) == 0
        assert "⣿" in out.read_text(encoding="utf-8")

    def test_dither_flag(self, tmp_path, capsys):
        path = self.make_image(tmp_path)
        assert self.run_cli(str(path), "--width", "10", "--dither") == 0
        assert "⣿" in capsys.readouterr().out

    def test_missing_image(self, tmp_path, capsys):
        assert self.run_cli(str(tmp_path / "nope.png")) == 1
        assert "not found" in capsys.readouterr().err

    def test_invalid_threshold(self, tmp_path, capsys):
        path = self.make_image(tmp_path)
        assert self.run_cli(str(path), "--threshold", "300") == 1
        assert "threshold" in capsys.readouterr().err

    def test_invalid_width(self, tmp_path, capsys):
        path = self.make_image(tmp_path)
        assert self.run_cli(str(path), "--width", "0") == 1
        assert "width" in capsys.readouterr().err

    def test_unreadable_image(self, tmp_path, capsys):
        path = tmp_path / "bad.png"
        path.write_text("not an image", encoding="utf-8")
        assert self.run_cli(str(path)) == 1
        assert "cannot open" in capsys.readouterr().err
