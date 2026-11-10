#!/usr/bin/env python3

import argparse
import pathlib
import sys

from PIL import Image

from inky.auto import auto

parser = argparse.ArgumentParser()

parser.add_argument("--saturation", "-s", type=float, default=0.5, help="Colour palette saturation")
parser.add_argument("--file", "-f", type=pathlib.Path, help="Image file")

inky = auto(ask_user=True, verbose=True)

args, _ = parser.parse_known_args()

saturation = args.saturation

if not args.file:
    print(f"""Usage:
    {sys.argv[0]} --file image.png (--saturation 0.5)""")
    sys.exit(1)

image = Image.open(args.file)
resizedimage = image.resize(inky.resolution)

# inky quantizes through a palette image it never loads, which Pillow 13 rejects
# ("ValueError: empty palette"). Dither to the display's palette here instead;
# set_image() takes a P image as it is.
if resizedimage.mode != "P" and hasattr(inky, "_palette_blend"):
    palette = inky._palette_blend(saturation)
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette + [0, 0, 0] * (256 - len(palette) // 3))
    resizedimage = resizedimage.convert("RGB").quantize(palette=palette_image)

try:
    inky.set_image(resizedimage, saturation=saturation)
except TypeError:
    inky.set_image(resizedimage)

inky.show()
