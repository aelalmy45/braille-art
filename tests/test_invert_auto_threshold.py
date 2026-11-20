"""Tests for --invert and the automatic (Otsu) threshold."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from braille_art import image_to_braille


def half_image(width: int = 4, height: int = 8) -> Image.Image:
    """Left half black (0), right half white (255)."""
    image = Image.new("L", (width, height), 255)
    for x in range(width // 2):
        for y in range(height):
            image.putpixel((x, y), 0)
    return image


class TestOtsuThreshold:
    def test_bimodal_image_splits_between_peaks(self):
        image = Image.new("L", (16, 8))
        for y in range(8):
            for x in range(16):
                image.putpixel((x, y), 50 if x < 8 else 200)
        threshold = image_to_braille.otsu_threshold(image)
        assert 50 < threshold <= 200

    def test_uniform_image_returns_valid_threshold(self):
        image = Image.new("L", (16, 8), 100)
        threshold = image_to_braille.otsu_threshold(image)
        assert 0 <= threshold <= 255

    def test_dark_photo_gets_low_threshold(self):
        dark = Image.new("L", (32, 32), 30)
        for y in range(16):
            for x in range(32):
                dark.putpixel((x, y), 60)
        bright = dark.point(lambda v: v + 150)
        assert image_to_braille.otsu_threshold(dark) < image_to_braille.otsu_threshold(bright)


class TestAutoThresholdConvert:
    def test_auto_threshold_matches_known_output(self):
        result = image_to_braille.convert(half_image(), 2)
        assert result == "⣿⠀\n⣿⠀"

    def test_auto_threshold_matches_explicit_otsu(self):
        image = Image.new("L", (16, 16))
        for y in range(16):
            for x in range(16):
                image.putpixel((x, y), round(255 * x / 15))
        prepared = image_to_braille.resize_image(
            image_to_braille.prepare_image(image),
            8,
        )
        expected = image_to_braille.otsu_threshold(prepared)
        assert image_to_braille.convert(image, 8) == image_to_braille.convert(
            image, 8, expected
        )


class TestInvert:
    def test_inverts_dot_choice(self):
        normal = image_to_braille.convert(half_image(), 2, 145)
        inverted = image_to_braille.convert(half_image(), 2, 145, invert=True)
        assert normal == "⣿⠀\n⣿⠀"
        assert inverted == "⠀⣿\n⠀⣿"

    def test_black_image_inverts_to_blank(self):
        black = Image.new("L", (4, 8), 0)
        result = image_to_braille.convert(black, 2, 145, invert=True)
        assert "⣿" not in result

    def test_white_image_inverts_to_all_dots(self):
        white = Image.new("L", (4, 8), 255)
        result = image_to_braille.convert(white, 2, 145, invert=True)
        assert result == "⣿⣿\n⣿⣿"

    def test_invert_with_dither(self):
        black = Image.new("L", (4, 8), 0)
        result = image_to_braille.convert(black, 2, dither=True, invert=True)
        assert "⣿" not in result

    def test_invert_with_auto_threshold(self):
        result = image_to_braille.convert(half_image(), 2, invert=True)
        assert result == "⠀⣿\n⠀⣿"


class TestCli:
    def make_image(self, tmp_path: Path) -> Path:
        path = tmp_path / "img.png"
        half_image(20, 20).save(path)
        return path

    def run_cli(self, *argv: str) -> int:
        sys.argv = ["braille-art", *argv]
        return image_to_braille.main()

    def test_invert_flag(self, tmp_path, capsys):
        path = self.make_image(tmp_path)
        assert self.run_cli(str(path), "--width", "10", "--invert") == 0
        out = capsys.readouterr().out
        assert "⣿" in out

    def test_no_threshold_uses_auto(self, tmp_path, capsys):
        path = self.make_image(tmp_path)
        assert self.run_cli(str(path), "--width", "10") == 0
        assert "⣿" in capsys.readouterr().out
