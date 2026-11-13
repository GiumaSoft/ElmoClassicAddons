"""Generate original moon/backpack line icons for the Sigillo footer (stdlib)."""
from math import hypot
from pathlib import Path
import struct

SIZE, DISPLAY_SIZE = 64, 14


def rounded_box(x, y, cx, cy, half_width, half_height, radius):
    qx, qy = abs(x - cx) - half_width + radius, abs(y - cy) - half_height + radius
    return hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius


def moon(x, y):
    # Outline of a crescent: one circle with a smaller overlapping circle cut out.
    shape = max(hypot(x - 7, y - 7) - 5.2, 4.8 - hypot(x - 9.3, y - 4.7))
    return abs(shape) - .55


def backpack(x, y):
    body = abs(rounded_box(x, y, 7, 8.2, 4, 4.2, 1.6)) - .55
    pocket = abs(rounded_box(x, y, 7, 9.8, 2.3, 1.5, .7)) - .45
    # Only the handle's upper half extends above the body.
    handle = max(abs(hypot(x - 7, y - 4) - 2) - .55, y - 4)
    return min(body, pocket, handle)


def generate():
    output = Path(__file__).resolve().parents[1] / 'ElmoLeveling/Media'
    output.mkdir(exist_ok=True)
    header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 8)
    for name, distance in [('Moon.tga', moon), ('Backpack.tga', backpack)]:
        pixels = bytearray()
        # Conventional bottom-left TGA origin, white artwork with soft alpha.
        for y in reversed(range(SIZE)):
            for x in range(SIZE):
                edge = distance((x + .5) * DISPLAY_SIZE / SIZE, (y + .5) * DISPLAY_SIZE / SIZE)
                alpha = round(max(0, min(1, .5 - edge)) * 255)
                pixels.extend((255, 255, 255, alpha))
        path = output / name
        path.write_bytes(header + pixels)
        print(path)


if __name__ == '__main__':
    generate()
