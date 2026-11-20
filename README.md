# Braille Art

[![tests](https://github.com/aelalmy45/braille-art/actions/workflows/tests.yml/badge.svg)](https://github.com/aelalmy45/braille-art/actions/workflows/tests.yml)

Command-line tools for turning images into Unicode Braille art and resizing
existing Braille art.

The output is plain Unicode text, so it works anywhere text does:

- Terminals and TUI applications
- Neovim and other editors
- Shell scripts and Python programs
- READMEs, logos, and banners

## Installation

Install with [pipx](https://pipx.pypa.io/) (recommended) or pip:

```bash
pipx install git+https://github.com/aelalmy45/braille-art.git
```

This provides two commands:

- `braille-art` — convert an image to Braille art
- `braille-scale` — resize existing Braille art

To install from a local clone instead:

```bash
pip install .
```

You can also run the scripts directly from a clone without installing
(requires `Pillow`, install it with `pip install Pillow`):

```bash
python image-to-braille.py photo.jpg
python braille-scale.py logo.txt
```

## Requirements

- Python 3.9+
- Pillow (installed automatically by pip/pipx)

## Usage

### Convert an image to Braille

```bash
braille-art photo.jpg
```

The default width is 80 Braille characters.

#### Width

```bash
braille-art photo.jpg --width 70
```

#### Threshold

By default the threshold that decides which pixels become filled Braille
dots is detected automatically with
[Otsu's method](https://en.wikipedia.org/wiki/Otsu%27s_method), which works
well for most images. Use `--threshold` (0–255) to set it yourself. Lower
values produce fewer filled dots, higher values produce more:

```bash
braille-art photo.jpg --width 70 --threshold 120
braille-art photo.jpg --width 70 --threshold 170
```

#### Invert

Dots are drawn for the dark parts of the image. If the result looks swapped
on your terminal (for example a dark image on a dark terminal), use
`--invert` to draw dots for the bright parts instead:

```bash
braille-art photo.jpg --invert
```

#### Color

Use `--color` to render the art in ANSI 24-bit color. Each drawn cell gets
the average color of the source pixels under its dots:

```bash
braille-art photo.jpg --color
```

Color works together with `--dither` and `--invert`. When writing to a file
with `--output`, the ANSI escape codes are kept; view the file with `cat`
to see the colors.

#### Dithering

Use `--dither` to apply Floyd–Steinberg dithering instead of a flat
threshold:

```bash
braille-art photo.jpg --dither
```

Dithering preserves shading and usually gives much better results for photos
and images with gradients. When `--dither` is enabled, `--threshold` is
ignored.

#### Save output

Use `--output` (or `-o`). The output file is overwritten on every run:

```bash
braille-art photo.jpg --width 70 --threshold 145 --output logo.txt
```

### Resize Braille art

```bash
braille-scale logo.txt
```

The default scale is 0.75. Pass a scale factor greater than 0 and up to 1:

```bash
braille-scale logo.txt 0.50
braille-scale logo.txt 0.25
```

Save the scaled version with `--output`:

```bash
braille-scale logo.txt 0.50 --output small-logo.txt
```

### Typical workflow

```bash
braille-art photo.jpg --width 70 --threshold 145 --output logo.txt
braille-scale logo.txt 0.50 --output small-logo.txt
```

### Help and version

```bash
braille-art --help
braille-scale --help
braille-art --version
```

## Project structure

```text
braille-art/
├── braille_art/          # the installable package
│   ├── __init__.py
│   ├── image_to_braille.py
│   └── braille_scale.py
├── tests/                # pytest suite
├── .github/workflows/    # CI: tests on push and pull requests
├── image-to-braille.py   # direct-run wrapper (braille-art)
├── braille-scale.py      # direct-run wrapper (braille-scale)
├── pyproject.toml
└── README.md
```

## Development

Install the package in editable mode with the test dependencies, then run
the test suite:

```bash
pip install -e .[dev]
pytest
```

Tests run automatically on every push and pull request (Python 3.9–3.13).

## How it works

Each Unicode Braille character represents a 2 × 4 block of 8 dots:

```text
1 4
2 5
3 6
7 8
```

Image conversion pipeline:

```text
Image → Grayscale → Contrast normalization → Resize → Auto threshold/Dither → Braille
```

Scaling pipeline:

```text
Braille → Decode → Crop → Area resize → Encode → Braille
```

Because the tools decode Braille into its dot bitmap, art can be resized
while preserving the structure of the Braille cells.

## Notes

- Input images are converted to grayscale with automatic contrast
  normalization.
- Image dimensions are adjusted for terminal character proportions.
- Empty borders are removed during scaling.
- Output files are overwritten, not appended.
- No dependency on any specific editor or terminal.
