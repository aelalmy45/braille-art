# Braille Art

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

The threshold controls which pixels become filled Braille dots (0–255,
default 145). Lower values produce fewer filled dots, higher values produce
more:

```bash
braille-art photo.jpg --width 70 --threshold 120
braille-art photo.jpg --width 70 --threshold 170
```

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
├── image-to-braille.py   # direct-run wrapper (braille-art)
├── braille-scale.py      # direct-run wrapper (braille-scale)
├── pyproject.toml
└── README.md
```

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
Image → Grayscale → Contrast normalization → Resize → Threshold/Dither → Braille
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
