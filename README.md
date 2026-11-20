# Braille Art

Small command-line utilities for creating and manipulating Unicode Braille art.

The project is designed to be simple, portable, and useful from any environment:

- Terminal
- TUI applications
- Neovim
- Shell scripts
- Python programs
- README/documentation
- ASCII/Braille logos and banners

There is no dependency on any specific editor or terminal environment.

---

## Tools

### `image-to-braille.py`

Converts an image into Unicode Braille art.

```text
Image
  ↓
Grayscale
  ↓
Contrast normalization
  ↓
Resize
  ↓
Threshold
  ↓
Braille
```

### `braille-scale.py`

Resizes existing Unicode Braille art.

```text
Braille
  ↓
Decode
  ↓
Crop
  ↓
Area resize
  ↓
Encode
  ↓
Braille
```

---

# Installation

Install with pipx (recommended) or pip:

```bash
pipx install git+https://github.com/aelalmy45/braille-art.git
```

Or from a local clone:

```bash
pip install .
```

This provides two commands:

- `braille-art` — convert an image to Braille art
- `braille-scale` — resize existing Braille art

Running from a clone without installing still works too (`Pillow` must be installed):

```bash
python image-to-braille.py photo.jpg
python braille-scale.py logo.txt
```

---

# Requirements

Python 3 and Pillow.

Install Pillow if needed:

```bash
pip install Pillow
```

---

# Image → Braille

Basic usage:

```bash
braille-art photo.jpg
```

The default width is `80` Braille characters.

---

## Set width

```bash
braille-art photo.jpg --width 70
```

For example:

```bash
braille-art photo.jpg --width 70
```

---

## Set threshold

The threshold controls which pixels become filled Braille dots.

Valid range:

```text
0 - 255
```

Example:

```bash
braille-art photo.jpg \
  --width 70 \
  --threshold 145
```

Some useful values to experiment with:

```bash
braille-art photo.jpg --width 70 --threshold 120
braille-art photo.jpg --width 70 --threshold 145
braille-art photo.jpg --width 70 --threshold 170
```

Lower values generally produce fewer filled pixels.

Higher values generally produce more filled pixels.

---

## Dithering

Use `--dither` to apply Floyd-Steinberg dithering instead of a flat threshold:

```bash
braille-art photo.jpg --dither
```

Dithering usually gives much better results for photos and images with
gradients, because it preserves shading that a flat threshold loses.

When `--dither` is enabled, `--threshold` is ignored.

---

# Save output

Use `--output` or `-o`:

```bash
braille-art photo.jpg \
  --width 70 \
  --threshold 145 \
  --output logo.txt
```

The output file is **overwritten** on every run.

For example:

```bash
braille-art photo.jpg \
  --width 70 \
  --threshold 170 \
  --output logo.txt
```

The previous contents of `logo.txt` are replaced by the new result.

The tool does not append old results.

---

# Scale Braille Art

Basic usage:

```bash
braille-scale logo.txt
```

The default scale is:

```text
0.75
```

---

## Scale to 50%

```bash
braille-scale logo.txt 0.50
```

## Scale to 60%

```bash
braille-scale logo.txt 0.60
```

## Scale to 25%

```bash
braille-scale logo.txt 0.25
```

The scale must be greater than `0` and less than or equal to `1`.

---

# Save scaled output

```bash
braille-scale \
  logo.txt \
  0.50 \
  --output small-logo.txt
```

The output file is overwritten if it already exists.

---

# Typical Workflow

A common workflow is:

```bash
braille-art \
  Photo.jpg \
  --width 70 \
  --threshold 145 \
  --output logo.txt
```

Then:

```bash
braille-scale \
  logo.txt \
  0.50
```

Or save the scaled version:

```bash
braille-scale \
  logo.txt \
  0.50 \
  --output small-logo.txt
```

---

# Command Help

If you forget how to use a command, use `--help`.

For image conversion:

```bash
braille-art --help
```

For scaling:

```bash
braille-scale --help
```

Version information:

```bash
braille-art --version
```

```bash
braille-scale --version
```

---

# Project Structure

```text
braille-art/
├── braille_art/          # the installable package
│   ├── __init__.py
│   ├── image_to_braille.py
│   └── braille_scale.py
├── image-to-braille.py   # direct-run wrapper (braille-art)
├── braille-scale.py      # direct-run wrapper (braille-scale)
├── pyproject.toml
├── README.md
└── logo.txt
```

`logo.txt` is only an example/output file. It is not required by the tools.

---

# Braille Structure

Each Unicode Braille character represents an 8-dot cell:

```text
1 4
2 5
3 6
7 8
```

Internally, the tools work with a `2 × 4` bitmap.

This allows Braille art to be resized while preserving the structure of the Braille cells.

---

# Design

The project intentionally stays small.

The core operations are:

```text
Image → Braille
Braille → Resize → Braille
```

There is currently no editor-specific integration.

The generated Braille can be used anywhere Unicode text can be displayed.

---

# Examples

Create a terminal-sized logo:

```bash
braille-art \
  Photo.jpg \
  --width 70 \
  --threshold 145
```

Create and save a logo:

```bash
braille-art \
  Photo.jpg \
  --width 70 \
  --threshold 145 \
  --output logo.txt
```

Create a smaller version:

```bash
braille-scale \
  logo.txt \
  0.50
```

Save the smaller version:

```bash
braille-scale \
  logo.txt \
  0.50 \
  --output small-logo.txt
```

---

# Notes

- Input images are converted to grayscale.
- Contrast is normalized automatically.
- Image dimensions are adjusted for terminal character proportions.
- Braille uses an 8-dot `2 × 4` structure.
- Empty borders are removed during Braille scaling.
- Output files are overwritten, not appended.
- The tools do not depend on Neovim, Zsh, or any specific terminal.
