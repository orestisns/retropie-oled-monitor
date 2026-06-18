#!/usr/bin/env python3
"""
OLED System Stats (128x64, SSD1306) - Screen 1.

Run on PC (window simulation):
    pip install luma.emulator pygame pillow psutil
    python oled_stats.py --emulate

Run on Raspberry Pi (real OLED over I2C):
    pip3 install luma.oled pillow psutil
    python3 oled_stats.py
"""
import os, sys, time, math, random

# Reuse the "logic" from the terminal script
from stats import cpu_temp, throttled_status, uptime_str
import psutil


def get_device(port=1):
    """Select device: emulator on PC, real SSD1306 on the Pi.

    port = the I2C bus number on the Pi:
        3 -> Screen 1 (system)  [software I2C, GPIO23/24]
        4 -> Screen 2 (game)    [software I2C, GPIO22/27]
    """
    if "--emulate" in sys.argv or os.name == "nt":
        from luma.emulator.device import pygame
        return pygame(width=128, height=64, scale=5, mode="1",
                      transform="smoothscale")
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    serial = i2c(port=port, address=0x3C)
    return ssd1306(serial, width=128, height=64)


class Toggle:
    """One button that cycles a screen through `pages` pages (0..pages-1).
    Real button on the Pi (BCM pin -> GND); auto-cycle on PC for preview."""
    def __init__(self, pin, pages=2):
        self.page = 0
        self.pages = pages
        self._auto_t = time.time()
        self._gpio = None
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING,
                                  callback=self._press, bouncetime=300)
            self._gpio = GPIO
        except Exception:
            self._gpio = None   # PC / no GPIO

    def _press(self, channel):
        self.page = (self.page + 1) % self.pages

    def poll(self):
        # No real button (PC) -> auto-cycle every 5s for preview
        if self._gpio is None and time.time() - self._auto_t > 5:
            self.page = (self.page + 1) % self.pages
            self._auto_t = time.time()


def throttle_short(txt):
    # Short code for the header
    if txt == "OK":
        return "OK"
    if txt == "N/A":
        return "--"
    if "UNDER" in txt:
        return "UV"      # under-voltage
    if "TEMP" in txt:
        return "TL"      # temp limit
    if "THROTTL" in txt:
        return "TH"      # throttled
    if "FREQ" in txt:
        return "FC"      # freq capped
    if "PAST" in txt:
        return "PE"      # past event
    return "!"


def draw_aperture(draw, cx, cy, R, r=None):
    # Aperture Science logo (camera-iris): solid white disc + black diaphragm
    if r is None:
        r = int(R * 0.42)
    draw.ellipse((cx - R, cy - R, cx + R, cy + R), fill="white")
    pts = []
    for i in range(6):
        a = math.radians(60 * i)
        ix = cx + r * math.cos(a)
        iy = cy + r * math.sin(a)
        a2 = math.radians(60 * i + 60)
        ox = cx + R * math.cos(a2)
        oy = cy + R * math.sin(a2)
        draw.line((ix, iy, ox, oy), fill="black")
        pts.append((ix, iy))
    draw.polygon(pts, fill="black")


# Half-Life logo - exact coordinates from the official SVG (viewBox 364.707)
_HL_VB_CENTER = 182.3535
_HL_LAMBDA = [
    (223.864, 272.729), (185.256, 174.881), (128.653, 264.065),
    (93.166, 264.065), (172.218, 136.411), (163.343, 111.182),
    (132.562, 111.182), (132.562, 81.120), (185.253, 81.120),
    (245.774, 235.019), (272.382, 226.351), (281.249, 256.164),
]
_HL_RING_R = 155.425
_HL_RING_W = 34.0


def pixel_reveal(device, render_fn, hold=5.0, steps=60, frame_delay=0.03):
    # Draw with render_fn(draw) and reveal the pixels in random order
    from PIL import Image, ImageDraw
    full = Image.new("1", (device.width, device.height))
    render_fn(ImageDraw.Draw(full))
    pixels = [(x, y) for y in range(device.height)
              for x in range(device.width) if full.getpixel((x, y))]
    random.shuffle(pixels)

    out = Image.new("1", (device.width, device.height))
    od = ImageDraw.Draw(out)
    per = max(1, len(pixels) // steps)
    i = 0
    while i < len(pixels):
        for _ in range(per):
            if i < len(pixels):
                od.point(pixels[i], fill=1)
                i += 1
        device.display(out)
        time.sleep(frame_delay)
    device.display(full)
    time.sleep(hold)


def draw_halflife(draw, cx, cy, size):
    # size = overall logo size in pixels. Monochrome (white) for OLED.
    s = size / 364.707
    r = _HL_RING_R * s
    w = max(2, round(_HL_RING_W * s))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline="white", width=w)
    pts = [(cx + (x - _HL_VB_CENTER) * s, cy + (y - _HL_VB_CENTER) * s)
           for x, y in _HL_LAMBDA]
    draw.polygon(pts, fill="white")


def render_boot_lines(device, font, shown):
    from luma.core.render import canvas
    with canvas(device) as draw:
        y = 0
        for label, res in shown:
            draw.text((0, y), ">" + label, font=font, fill="white")
            if res:
                draw.text((116 - len(res) * 6, y), res, font=font, fill="white")
            y += 11


def boot_sequence(device, font):
    # Boot lines: time spread across the checks, holds 3s at the end
    # [label, result, delay] - the delay after each step
    lines = [
        ["INIT SYSTEM", "OK", 1.5],
        ["CPU SENSORS", "OK", 1.2],
        ["MEMORY", "OK", 1.8],
        ["RADIATION", "!", 1.2],
        ["SYSTEM READY", "", 3.0],
    ]
    shown = []
    for label, res, delay in lines:
        shown.append([label, res])
        render_boot_lines(device, font, shown)
        if res == "!":
            for _ in range(2):
                shown[-1][1] = ""
                render_boot_lines(device, font, shown)
                time.sleep(0.28)
                shown[-1][1] = "!"
                render_boot_lines(device, font, shown)
                time.sleep(0.28)
        time.sleep(delay)


def ctext(draw, font, y, text):
    # centered text (default font ~6px/char)
    draw.text(((128 - len(text) * 6) // 2, y), text, font=font, fill="white")


def splash(device, font, hold=5.0):
    # Half-Life logo with pixel-reveal animation (size=67 -> 58px, same as aperture)
    pixel_reveal(device, lambda d: draw_halflife(d, 64, 32, 67), hold=hold)


def draw_bar(draw, x, y, w, h, pct):
    pct = max(0.0, min(100.0, pct))
    draw.rectangle((x, y, x + w, y + h), outline="white", fill="black")
    fillw = int((w - 2) * pct / 100.0)
    if fillw > 0:
        draw.rectangle((x + 1, y + 1, x + 1 + fillw, y + h - 1),
                       outline="white", fill="white")


def row(draw, font, y, label, value, pct):
    draw.text((4, y), label, font=font, fill="white")
    draw_bar(draw, 26, y + 1, 70, 6, pct)
    draw.text((100, y), value, font=font, fill="white")


# Throttle code reference (shown as pages 2 & 3 on the system screen)
THR_ENTRIES = [
    ("OK", "all good"),
    ("UV", "under-volt"),
    ("FC", "freq cap"),
    ("TH", "throttled"),
    ("TL", "temp limit"),
    ("PE", "past event"),
    ("--", "N/A"),
]


def draw_throttle_page(draw, font, p):
    # p = 0 -> entries 0..3, p = 1 -> entries 4..6
    draw.text((4, 2), f"THROTTLE  {p + 1}/2", font=font, fill="white")
    draw.line((4, 12, 123, 12), fill="white")
    y = 16
    for code, meaning in THR_ENTRIES[p * 4:(p + 1) * 4]:
        draw.text((4, y), f"{code}  {meaning}", font=font, fill="white")
        y += 12


def stats_loop(device, font, pager=None):
    # Live system stats with button paging (no boot/splash)
    # pages: 0 = stats, 1 = throttle table 1/2, 2 = throttle table 2/2
    from luma.core.render import canvas

    if pager is None:
        pager = Toggle(5, pages=3)     # GPIO5 -> screen 1 (system)

    while True:
        pager.poll()
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
        temp = cpu_temp()                      # float C or None
        thr_txt, _ = throttled_status()

        temp_pct = (temp / 80.0 * 100.0) if temp is not None else 0.0
        temp_val = f"{temp:.0f}C" if temp is not None else "--"

        with canvas(device) as draw:
            if pager.page == 1:
                draw_throttle_page(draw, font, 0)
            elif pager.page == 2:
                draw_throttle_page(draw, font, 1)
            else:
                # Header: uptime on the left + throttle code on the right
                draw.text((4, 2), f"UP {uptime_str()}", font=font, fill="white")
                thr_code = "T:" + throttle_short(thr_txt)
                draw.text((124 - len(thr_code) * 6, 2), thr_code, font=font, fill="white")
                draw.line((4, 12, 123, 12), fill="white")

                row(draw, font, 16, "CPU", f"{cpu:.0f}%", cpu)
                row(draw, font, 28, "TMP", temp_val, temp_pct)
                row(draw, font, 40, "RAM", f"{mem.percent:.0f}%", mem.percent)
                row(draw, font, 52, "DSK", f"{disk.percent:.0f}%", disk.percent)

        time.sleep(1)


def run(device, font):
    # Boot -> splash -> live system stats (standalone)
    boot_sequence(device, font)
    splash(device, font, hold=5.0)
    stats_loop(device, font)


def main():
    from PIL import ImageFont
    device = get_device(port=3)        # Screen 1 (system) -> /dev/i2c-3
    run(device, ImageFont.load_default())


if __name__ == "__main__":
    main()
