#!/usr/bin/env python3
"""
Run the braille-scale CLI directly from a source checkout.

The same functionality is installed as the `braille-scale` command
when the package is installed with pip or pipx.
"""

from braille_art.braille_scale import main

if __name__ == "__main__":
    raise SystemExit(main())
