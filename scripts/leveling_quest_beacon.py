"""Draw the original ElmoLeveling quest beacon at twice its in-game size."""
from math import exp, hypot, sqrt
from pathlib import Path
from struct import pack


WIDTH, HEIGHT, SCALE = 64, 128, 2
CX, BADGE_Y, BASE_Y = 32, 16, 112


def glow(distance, radius):
    return exp(-(distance / radius) ** 2)


def pixel(x, y):
    dx, dy = x - CX, y - BASE_Y
    radius = hypot(dx, y - BADGE_Y)
    r, g, b, a = 0, 0, 0, 0

    def paint(color, opacity):
        nonlocal r, g, b, a
        opacity = max(0, min(1, opacity))
        retain = 1 - opacity
        r = color[0] * opacity + r * retain
        g = color[1] * opacity + g * retain
        b = color[2] * opacity + b * retain
        a = opacity + a * retain

    # Cool reflected light, two elliptical contours, and a bright center.
    ellipse = sqrt((dx / 25) ** 2 + (dy / 6) ** 2)
    paint((44, 108, 208), .45 * glow(ellipse, 1.15))
    paint((98, 173, 237), .8 * glow(ellipse - 1, .09))
    paint((178, 226, 255), .95 * glow(ellipse - .65, .085))
    paint((210, 241, 255), .9 * glow(hypot(dx / 5, dy / 2), 1))

    if BADGE_Y <= y <= BASE_Y:
        progress = (y - BADGE_Y) / (BASE_Y - BADGE_Y)
        paint((67, 145, 251), .62 * glow(dx, 5.5 - progress))
        paint((151, 223, 255), .96 * glow(dx, 2.5 - progress * .55))
        paint((246, 253, 255), glow(dx, 1.1))

    # A bronze rim ties the dark medallion to ElmoLeveling's tracker.
    paint((100, 182, 255), .65 * glow(radius - 11, 2.8))
    paint((10, 23, 41), min(1, (10.8 - radius) * SCALE + .5))
    paint((242, 198, 120), .95 * glow(radius - 10.7, .74))
    paint((107, 176, 231), .66 * glow(radius - 12.3, .56))
    edge_fade = min(1, x / 5, (WIDTH - x) / 5, y / 4, (HEIGHT - y) / 4)
    if a * edge_fade < 1 / 255:
        return bytes(4)
    return bytes((round(b / a), round(g / a), round(r / a), round(a * edge_fade * 255)))


if __name__ == "__main__":
    media = Path(__file__).resolve().parents[1] / "ElmoLeveling" / "Media"
    width, height = WIDTH * SCALE, HEIGHT * SCALE
    header = pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, width, height, 32, 0x28)
    data = b"".join(pixel((x + .5) / SCALE, (y + .5) / SCALE) for y in range(height) for x in range(width))
    (media / "QuestBeacon.tga").write_bytes(header + data)
