"""Generate ElmoLeveling's own 64px rounded nine-slice TGA, without dependencies."""
from math import hypot
from pathlib import Path
import struct

SIZE, RADIUS, SAMPLES = 64, 10, 4
BACKGROUND, BORDER = (18, 18, 16), (81, 67, 43)


def distance(x, y):
    qx = abs(x - SIZE / 2) - (SIZE / 2 - RADIUS)
    qy = abs(y - SIZE / 2) - (SIZE / 2 - RADIUS)
    return hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - RADIUS


def generate():
    pixels = bytearray()
    for y in range(SIZE):
        for x in range(SIZE):
            total, colors = 0, [0, 0, 0]
            for sy in range(SAMPLES):
                for sx in range(SAMPLES):
                    edge = distance(x + (sx + .5) / SAMPLES, y + (sy + .5) / SAMPLES)
                    if edge > 0:
                        continue
                    color = BORDER if edge >= -1 else BACKGROUND
                    total += 1
                    colors = [a + b for a, b in zip(colors, color)]
            rgb = [round(c / total) if total else 0 for c in colors]
            pixels.extend((*reversed(rgb), round(255 * total / SAMPLES**2)))
    # Uncompressed, 32-bit BGRA, top-left origin, eight alpha bits.
    header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 0x28)
    output = Path(__file__).resolve().parents[1] / 'ElmoLeveling/Media/Panel.tga'
    output.parent.mkdir(exist_ok=True)
    output.write_bytes(header + pixels)
    print(output)


if __name__ == '__main__':
    generate()
