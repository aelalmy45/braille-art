#!/usr/bin/env python3
"""
Run the image-to-braille CLI directly from a source checkout.

The same functionality is installed as the `braille-art` command
when the package is installed with pip or pipx.
"""

from braille_art.image_to_braille import main

if __name__ == "__main__":
    raise SystemExit(main())
