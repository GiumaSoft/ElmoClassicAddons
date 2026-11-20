"""Draw the original ElmoLeveling compass arrow as an antialiased WoW texture."""
from pathlib import Path
from struct import pack


SIZE = 64
SAMPLES = 4
FACES = (
    (((32, 4), (56, 55), (32, 43)), (50, 27, 26)),
    (((32, 4), (32, 43), (8, 55)), (50, 27, 26)),
    (((32, 8), (52, 51), (32, 39)), (187, 115, 42)),
    (((32, 8), (32, 39), (12, 51)), (255, 217, 125)),
    (((32, 8), (38, 28), (32, 39), (26, 28)), (253, 186, 74)),
    (((32, 8), (32, 39), (26, 28)), (255, 237, 167)),
)


def covers(polygon, x, y):
    edges = zip(polygon, polygon[1:] + polygon[:1])
    cross = [(bx - ax) * (y - ay) - (by - ay) * (x - ax) for (ax, ay), (bx, by) in edges]
    return all(c >= 0 for c in cross) or all(c <= 0 for c in cross)


def pixel(x, y):
    colors = []
    for offset_y in range(SAMPLES):
        for offset_x in range(SAMPLES):
            sx = x + (offset_x + 0.5) / SAMPLES
            sy = y + (offset_y + 0.5) / SAMPLES
            for shape, color in reversed(FACES):
                if covers(shape, sx, sy):
                    colors.append(color)
                    break
    if not colors:
        return bytes(4)
    r, g, b = (sum(channel) // len(colors) for channel in zip(*colors))
    return bytes((b, g, r, round(255 * len(colors) / SAMPLES**2)))


if __name__ == "__main__":
    media = Path(__file__).resolve().parents[1] / "ElmoLeveling" / "Media"
    header = pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 0x28)
    (media / "QuestArrow.tga").write_bytes(header + b"".join(pixel(x, y) for y in range(SIZE) for x in range(SIZE)))
