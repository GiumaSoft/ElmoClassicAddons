"""Generate original antialiased Sigillo ring/mask textures using only stdlib."""
from math import hypot
from pathlib import Path
import struct

SIZE, DISPLAY_SIZE = 256, 76


def generate():
    output = Path(__file__).resolve().parents[1] / 'ElmoLeveling/Media'
    output.mkdir(exist_ok=True)
    # One display-pixel alpha falloff remains smooth at the native UI size.
    rings, masks = bytearray(), bytearray()
    for y in range(SIZE):
        dy = (y + .5 - SIZE / 2) * DISPLAY_SIZE / SIZE
        for x in range(SIZE):
            dx = (x + .5 - SIZE / 2) * DISPLAY_SIZE / SIZE
            alpha = max(0, min(1, 2 - abs(hypot(dx, dy) - 36)))
            rings.extend((255, 255, 255, round(alpha * 255)))
            masks.extend((255, 255, 255, round(max(0, min(1, dy + .5)) * 255)))
    # Uncompressed, 32-bit BGRA, top-left origin, eight alpha bits.
    header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 0x28)
    for name, pixels in [('Ring.tga', rings), ('RingMask.tga', masks)]:
        path = output / name
        path.write_bytes(header + pixels)
        print(path)


if __name__ == '__main__':
    generate()
