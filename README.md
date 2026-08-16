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
python image-to-braille.py photo.jpg
```

The default width is `80` Braille characters.

---

## Set width

```bash
python image-to-braille.py photo.jpg --width 70
```

For example:

```bash
python image-to-braille.py photo.jpg --width 70
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
python image-to-braille.py photo.jpg \
  --width 70 \
  --threshold 145
```

Some useful values to experiment with:

```bash
python image-to-braille.py photo.jpg --width 70 --threshold 120
python image-to-braille.py photo.jpg --width 70 --threshold 145
python image-to-braille.py photo.jpg --width 70 --threshold 170
```

Lower values generally produce fewer filled pixels.

Higher values generally produce more filled pixels.

---

# Save output

Use `--output` or `-o`:

```bash
python image-to-braille.py photo.jpg \
  --width 70 \
  --threshold 145 \
  --output logo.txt
```

The output file is **overwritten** on every run.

For example:

```bash
python image-to-braille.py photo.jpg \
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
python braille-scale.py logo.txt
```

The default scale is:

```text
0.75
```

---

## Scale to 50%

```bash
python braille-scale.py logo.txt 0.50
```

## Scale to 60%

```bash
python braille-scale.py logo.txt 0.60
```

## Scale to 25%

```bash
python braille-scale.py logo.txt 0.25
```

The scale must be greater than `0` and less than or equal to `1`.

---

# Save scaled output

```bash
python braille-scale.py \
  logo.txt \
  0.50 \
  --output small-logo.txt
```

The output file is overwritten if it already exists.

---

# Typical Workflow

A common workflow is:

```bash
python image-to-braille.py \
  Photo.jpg \
  --width 70 \
  --threshold 145 \
  --output logo.txt
```

Then:

```bash
python braille-scale.py \
  logo.txt \
  0.50
```

Or save the scaled version:

```bash
python braille-scale.py \
  logo.txt \
  0.50 \
  --output small-logo.txt
```

---

# Command Help

If you forget how to use a command, use `--help`.

For image conversion:

```bash
python image-to-braille.py --help
```

For scaling:

```bash
python braille-scale.py --help
```

Version information:

```bash
python image-to-braille.py --version
```

```bash
python braille-scale.py --version
```

---

# Project Structure

```text
braille-art/
├── image-to-braille.py
├── braille-scale.py
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
python image-to-braille.py \
  Photo.jpg \
  --width 70 \
  --threshold 145
```

Create and save a logo:

```bash
python image-to-braille.py \
  Photo.jpg \
  --width 70 \
  --threshold 145 \
  --output logo.txt
```

Create a smaller version:

```bash
python braille-scale.py \
  logo.txt \
  0.50
```

Save the smaller version:

```bash
python braille-scale.py \
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
