"""Tests for braille_art.braille_scale."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from braille_art import braille_scale


def make_bitmap(width: int, height: int, on: list[tuple[int, int]]) -> list[list[bool]]:
    bitmap = [[False] * width for _ in range(height)]
    for x, y in on:
        bitmap[y][x] = True
    return bitmap


class TestEncodeDecodeRoundTrip:
    def test_single_cell_all_dots(self):
        bitmap = make_bitmap(2, 4, [(x, y) for x in range(2) for y in range(4)])
        lines = braille_scale.encode(bitmap)
        assert lines == ["⣿"]
        assert braille_scale.decode(lines)[0:4] == bitmap

    def test_empty_cell(self):
        bitmap = make_bitmap(2, 4, [])
        lines = braille_scale.encode(bitmap)
        assert lines == [""]
        decoded = braille_scale.decode(["⠀"])
        assert decoded == bitmap

    def test_each_dot_bit(self):
        # Each of the 8 dots, one at a time, must survive the round trip.
        for dx, dy, _bit in braille_scale.DOTS:
            bitmap = make_bitmap(2, 4, [(dx, dy)])
            lines = braille_scale.encode(bitmap)
            assert braille_scale.decode(lines) == bitmap

    def test_multi_cell_round_trip(self):
        on = [(0, 0), (3, 1), (5, 7), (1, 11), (4, 4)]
        bitmap = make_bitmap(6, 12, on)
        lines = braille_scale.encode(bitmap)
        assert braille_scale.decode(lines) == bitmap

    def test_encode_rstrips_blank_cells(self):
        bitmap = make_bitmap(4, 4, [(0, 0)])
        assert braille_scale.encode(bitmap) == ["⠁"]

    def test_decode_ignores_non_braille(self):
        assert braille_scale.decode(["abc"]) == [[False] * 6 for _ in range(4)]


class TestCrop:
    def test_removes_empty_borders(self):
        bitmap = make_bitmap(6, 8, [(2, 3), (4, 5)])
        cropped = braille_scale.crop(bitmap)
        assert len(cropped) == 3  # rows 3..5
        assert len(cropped[0]) == 3  # cols 2..4
        assert cropped[0][0] is True  # (2, 3)
        assert cropped[2][2] is True  # (4, 5)

    def test_all_empty(self):
        bitmap = make_bitmap(4, 4, [])
        assert braille_scale.crop(bitmap) == bitmap


class TestResize:
    def test_dimensions_follow_braille_cells(self):
        bitmap = make_bitmap(20, 40, [(0, 0)])
        resized = braille_scale.resize(bitmap, 0.5)
        assert len(resized) % 4 == 0
        assert len(resized[0]) % 2 == 0
        assert len(resized) == 20
        assert len(resized[0]) == 10

    def test_minimum_size(self):
        bitmap = make_bitmap(100, 100, [(50, 50)])
        resized = braille_scale.resize(bitmap, 0.01)
        assert len(resized) == 4
        assert len(resized[0]) == 2

    def test_scale_one_keeps_content(self):
        on = [(0, 0), (3, 3), (1, 7)]
        bitmap = make_bitmap(4, 8, on)
        resized = braille_scale.resize(bitmap, 1.0)
        assert resized == bitmap

    def test_shrinking_a_solid_block_stays_solid(self):
        bitmap = make_bitmap(8, 16, [(x, y) for x in range(8) for y in range(16)])
        resized = braille_scale.resize(bitmap, 0.5)
        assert all(all(row) for row in resized)


class TestScaleBraille:
    def test_end_to_end(self):
        on = [(x, y) for x in range(8) for y in range(16)]
        bitmap = make_bitmap(8, 16, on)
        lines = braille_scale.encode(bitmap)
        scaled = braille_scale.scale_braille(lines, 0.5)
        assert scaled == ["⣿⣿"] * 2

    def test_blank_input(self):
        scaled = braille_scale.scale_braille(["⠀⠀"], 0.5)
        assert all(line == "" for line in scaled)


class TestCli:
    def write_art(self, tmp_path: Path) -> Path:
        art = tmp_path / "art.txt"
        art.write_text("⣿⣿⣿⣿\n" * 4, encoding="utf-8")
        return art

    def test_scales_to_stdout(self, tmp_path, capsys):
        art = self.write_art(tmp_path)
        sys.argv = ["braille-scale", str(art), "0.5"]
        assert braille_scale.main() == 0
        out = capsys.readouterr().out
        assert "⣿⣿" in out

    def test_output_file(self, tmp_path):
        art = self.write_art(tmp_path)
        out = tmp_path / "small.txt"
        sys.argv = ["braille-scale", str(art), "0.5", "--output", str(out)]
        assert braille_scale.main() == 0
        assert "⣿⣿" in out.read_text(encoding="utf-8")

    def test_missing_file(self, tmp_path, capsys):
        sys.argv = ["braille-scale", str(tmp_path / "nope.txt")]
        assert braille_scale.main() == 1
        assert "not found" in capsys.readouterr().err

    def test_invalid_scale(self, tmp_path, capsys):
        art = self.write_art(tmp_path)
        sys.argv = ["braille-scale", str(art), "1.5"]
        assert braille_scale.main() == 1
        assert "scale" in capsys.readouterr().err

    def test_no_braille_in_file(self, tmp_path, capsys):
        art = tmp_path / "plain.txt"
        art.write_text("hello\n", encoding="utf-8")
        sys.argv = ["braille-scale", str(art)]
        assert braille_scale.main() == 1
        assert "no Braille" in capsys.readouterr().err

    def test_default_scale(self, tmp_path, capsys):
        art = self.write_art(tmp_path)
        sys.argv = ["braille-scale", str(art)]
        assert braille_scale.main() == 0
        capsys.readouterr()
