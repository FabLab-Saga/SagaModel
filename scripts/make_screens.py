"""Generate our own laptop screen images for the work-table props (assets/screens/). System python3 + Pillow.
vector.png = a laser-cut box layout in a vector editor; code.png = microcontroller code + serial monitor."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "screens"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = ROOT / "refs" / "branding" / "fonts"
W, H = 1600, 1000


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def vector():
    im = Image.new("RGB", (W, H), (236, 236, 238))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 44], fill=(52, 54, 58))                       # title/menu bar
    d.text((16, 10), "box_living_hinge.svg  -  vector editor", fill=(230, 230, 230), font=font("Roboto-Regular.ttf", 22))
    d.rectangle([0, 44, 64, H], fill=(64, 66, 70))                      # tool column
    for k in range(10):
        d.rounded_rectangle([14, 70 + k * 58, 50, 106 + k * 58], 6, fill=(96, 98, 104))
    d.rectangle([W - 300, 44, W, H], fill=(246, 246, 247))              # layers panel
    d.text((W - 284, 64), "Layers", fill=(40, 40, 40), font=font("Roboto-Bold.ttf", 24))
    for k, (name, c) in enumerate((("cut", (220, 30, 30)), ("engrave", (30, 60, 220)), ("score", (20, 150, 90)))):
        y = 110 + k * 44
        d.rectangle([W - 284, y, W - 260, y + 24], fill=c)
        d.text((W - 248, y - 2), name, fill=(40, 40, 40), font=font("Roboto-Regular.ttf", 22))
    d.rectangle([110, 90, W - 340, H - 50], fill=(255, 255, 255), outline=(170, 170, 170))   # sheet 600 x 400
    red, blue = (220, 30, 30), (30, 60, 220)

    def finger_rect(x0, y0, w, h, n=6, t=12):
        pts = []
        for i in range(n * 2 + 1):                                       # top edge with fingers
            x = x0 + w * i / (n * 2)
            yy = y0 - (t if i % 2 else 0)
            pts += [(x, yy)] if i == 0 else [(x, pts[-1][1]), (x, yy)]
        pts += [(x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)]
        d.line(pts, fill=red, width=3)

    for k in range(3):
        finger_rect(160 + k * 350, 190, 300, 210)
    for k in range(2):
        finger_rect(160 + k * 350, 520, 300, 230)
    for k in range(18):                                                  # living hinge slots
        x = 870 + k * 14
        d.line([(x, 520 + (k % 2) * 30), (x, 520 + (k % 2) * 30 + 170)], fill=red, width=2)
    d.text((196, 272), "FAB LAB SAGA", fill=blue, font=font("RobotoCondensed-Bold.ttf", 40))
    return im


def code():
    im = Image.new("RGB", (W, H), (30, 32, 36))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 44], fill=(22, 23, 26))
    d.text((16, 10), "sensor_node.ino", fill=(220, 220, 220), font=font("Roboto-Regular.ttf", 22))
    d.rectangle([0, 44, W, 92], fill=(0, 120, 120))                     # toolbar
    for k in range(4):
        d.ellipse([16 + k * 54, 52, 50 + k * 54, 86], fill=(230, 240, 240))
    mono = font("RobotoCondensed-Regular.ttf", 26)
    kw, ty, st, cm, tx = (200, 120, 230), (90, 170, 240), (220, 170, 90), (110, 130, 110), (215, 215, 215)
    lines = [
        [(cm, "// Fab Lab SAGA - workshop sensor node")],
        [(kw, "#include "), (st, "<Wire.h>")],
        [(kw, "#include "), (st, "\"bme280.h\"")],
        [],
        [(ty, "const int "), (tx, "LED_PIN = "), (st, "13"), (tx, ";")],
        [(ty, "BME280 "), (tx, "sensor;")],
        [],
        [(ty, "void "), (tx, "setup() {")],
        [(tx, "  Serial.begin("), (st, "115200"), (tx, ");")],
        [(tx, "  pinMode(LED_PIN, OUTPUT);")],
        [(tx, "  sensor.begin("), (st, "0x76"), (tx, ");")],
        [(tx, "}")],
        [],
        [(ty, "void "), (tx, "loop() {")],
        [(ty, "  float "), (tx, "t = sensor.readTemperature();")],
        [(ty, "  float "), (tx, "h = sensor.readHumidity();")],
        [(tx, "  Serial.print("), (st, "\"T=\""), (tx, "); Serial.println(t);")],
        [(tx, "  digitalWrite(LED_PIN, t > "), (st, "24.0"), (tx, ");")],
        [(tx, "  delay("), (st, "1000"), (tx, ");")],
        [(tx, "}")],
    ]
    for i, segs in enumerate(lines):
        y = 104 + i * 34
        d.text((14, y), f"{i + 1:>2}", fill=(100, 100, 110), font=mono)
        x = 70
        for c, s in segs:
            d.text((x, y), s, fill=c, font=mono)
            x += d.textlength(s, font=mono)
    d.rectangle([0, H - 190, W, H], fill=(18, 19, 22))                  # serial monitor
    d.text((14, H - 182), "Serial Monitor  115200 baud", fill=(150, 150, 160), font=font("Roboto-Regular.ttf", 22))
    for i, v in enumerate(("T=21.84", "T=21.86", "T=21.85", "T=21.91")):
        d.text((14, H - 146 + i * 34), v, fill=(120, 220, 140), font=mono)
    return im


vector().save(OUT / "vector.png")
code().save(OUT / "code.png")
print("screens ->", OUT)
