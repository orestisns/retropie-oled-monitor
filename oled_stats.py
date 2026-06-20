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
import os, sys, time, math, random, threading

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
    """One button per screen.
      - short press        -> next page (cycles 0..pages-1)
      - long press (>=3s)  -> turn the screen off / on (toggles .power)
    Polls the GPIO in a background thread (reliable + debounced).
    On PC (no GPIO) the page auto-cycles for preview."""
    HOLD_SECS = 3.0
    POLL = 0.02         # 20 ms sampling
    DEBOUNCE = 0.04     # ignore presses shorter than this (switch bounce)

    def __init__(self, pin, pages=2):
        self.page = 0
        self.power = True          # screen on/off
        self.pages = pages
        self._pin = pin
        self._auto_t = time.time()
        self._gpio = None
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._gpio = GPIO
            threading.Thread(target=self._run, daemon=True).start()
        except Exception:
            self._gpio = None   # PC / no GPIO

    def _run(self):
        GPIO = self._gpio
        pressed = False
        t_press = 0.0
        long_done = False
        while True:
            level = GPIO.input(self._pin)      # 1 = released, 0 = pressed
            now = time.time()
            if not pressed and level == 0:
                pressed = True
                t_press = now
                long_done = False
            elif pressed and level == 0:
                # still held -> fire power toggle the moment 3s is reached
                if not long_done and now - t_press >= self.HOLD_SECS:
                    self.power = not self.power
                    long_done = True
            elif pressed and level == 1:
                pressed = False
                dur = now - t_press
                if long_done:
                    pass                        # already handled on hold
                elif dur < self.DEBOUNCE:
                    pass                        # bounce/noise -> ignore
                else:
                    self.page = (self.page + 1) % self.pages  # short -> next page
            time.sleep(self.POLL)

    def poll(self):
        # No real button (PC) -> auto-cycle every 5s for preview
        if self._gpio is None and time.time() - self._auto_t > 5:
            self.page = (self.page + 1) % self.pages
            self._auto_t = time.time()


def screen_off(device):
    # Power the OLED off (fallback: draw a blank/black frame)
    try:
        device.hide()
    except Exception:
        from luma.core.render import canvas
        with canvas(device):
            pass


def screen_on(device):
    try:
        device.show()
    except Exception:
        pass


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


def pixel_reveal(device, render_fn, hold=5.0, steps=60, frame_delay=0.015):
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
        ["INIT SYSTEM", "OK", 0.75],
        ["CPU SENSORS", "OK", 0.6],
        ["MEMORY", "OK", 0.9],
        ["RADIATION", "!", 0.6],
        ["SYSTEM READY", "", 1.5],
    ]
    shown = []
    for label, res, delay in lines:
        shown.append([label, res])
        render_boot_lines(device, font, shown)
        if res == "!":
            for _ in range(2):
                shown[-1][1] = ""
                render_boot_lines(device, font, shown)
                time.sleep(0.14)
                shown[-1][1] = "!"
                render_boot_lines(device, font, shown)
                time.sleep(0.14)
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


# Metric graph with X-Y axes (one page per metric)
AX_X = 20        # y-axis column (room for labels to its left)
AX_TOP = 12      # top of plot
AX_BOT = 60      # bottom of plot (x-axis)
AX_RIGHT = 126   # right edge of plot
GRAPH_W = AX_RIGHT - AX_X   # usable columns (time samples)


def draw_graph(draw, font, title, hist, cur_label, ymax_label="100"):
    # hist holds 0..100 values (percent of range). Newest pinned to the right.
    draw.text((0, 2), title, font=font, fill="white")
    draw.text((124 - len(cur_label) * 6, 2), cur_label, font=font, fill="white")

    # Axes
    draw.line((AX_X, AX_TOP, AX_X, AX_BOT), fill="white")        # Y axis
    draw.line((AX_X, AX_BOT, AX_RIGHT, AX_BOT), fill="white")    # X axis
    draw.text((AX_X - 1 - len(ymax_label) * 6, AX_TOP - 3), ymax_label,
              font=font, fill="white")
    draw.text((AX_X - 1 - 6, AX_BOT - 9), "0", font=font, fill="white")
    # mid gridline (50%)
    ymid = (AX_TOP + AX_BOT) // 2
    for x in range(AX_X + 2, AX_RIGHT, 4):
        draw.point((x, ymid), fill="white")

    data = hist[-GRAPH_W:]
    n = len(data)
    span = AX_BOT - AX_TOP
    pts = []
    for i, v in enumerate(data):
        x = AX_RIGHT - (n - 1 - i)
        y = AX_BOT - int(span * max(0.0, min(100.0, v)) / 100.0)
        pts.append((x, y))
    if len(pts) >= 2:
        draw.line(pts, fill="white")
    elif pts:
        draw.point(pts[0], fill="white")


def stats_loop(device, font, pager=None):
    # Live system stats with button paging (no boot/splash)
    # pages: 0=overview, 1=CPU, 2=TMP, 3=RAM, 4=DSK (graphs)
    from luma.core.render import canvas

    if pager is None:
        pager = Toggle(5, pages=5)     # GPIO5 -> screen 1 (system)

    cpu_hist, tmp_hist, ram_hist, dsk_hist = [], [], [], []
    off = False

    while True:
        pager.poll()
        if not pager.power:            # long-press turned the screen off
            if not off:
                screen_off(device)
                off = True
            time.sleep(0.3)
            continue
        if off:
            screen_on(device)
            off = False

        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
        temp = cpu_temp()                      # float C or None
        thr_txt, _ = throttled_status()

        temp_pct = (temp / 80.0 * 100.0) if temp is not None else 0.0
        temp_val = f"{temp:.0f}C" if temp is not None else "--"

        for h, v in ((cpu_hist, cpu), (tmp_hist, temp_pct),
                     (ram_hist, mem.percent), (dsk_hist, disk.percent)):
            h.append(v)
            if len(h) > GRAPH_W:
                del h[0]

        with canvas(device) as draw:
            p = pager.page
            if p == 1:
                draw_graph(draw, font, "CPU", cpu_hist, f"{cpu:.0f}%")
            elif p == 2:
                draw_graph(draw, font, "TMP", tmp_hist, temp_val, "80")
            elif p == 3:
                draw_graph(draw, font, "RAM", ram_hist, f"{mem.percent:.0f}%")
            elif p == 4:
                draw_graph(draw, font, "DSK", dsk_hist, f"{disk.percent:.0f}%")
            else:
                # Page 0: overview. Header: uptime + throttle code
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
