#!/usr/bin/env python3
"""
OLED Game / Emulation Stats (128x64, SSD1306) — Screen 2.

Διαβάζει την κατάσταση παιχνιδιού από αρχείο key=value:
    game=Super Mario Bros
    system=NES
    core=fceumm
    fps=59
    target=60
    status=PLAYING
    start=<epoch seconds>

Στο Pi το αρχείο το γράφει το runcommand-onstart.sh (βλ. σχόλια κάτω).

Τρέξιμο στο PC (προσομοίωση):
    python game_stats.py --emulate
Τρέξιμο στο Pi:
    python3 game_stats.py
"""
import os, sys, time

# Ξαναχρησιμοποιούμε τις γραφικές βοηθητικές από το screen 1
from oled_stats import get_device, draw_bar, ctext, draw_aperture

STATUS_FILE = os.environ.get(
    "GAME_STATUS_FILE",
    "game_status.txt" if os.name == "nt" else "/tmp/game_status",
)


def aperture_splash(device, font, hold=10.0):
    from luma.core.render import canvas
    with canvas(device) as draw:
        draw_aperture(draw, 64, 32, 28)
    time.sleep(hold)


def read_status():
    data = {}
    try:
        with open(STATUS_FILE) as f:
            for line in f:
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip()
    except Exception:
        pass
    return data


def fmt_play(start):
    try:
        secs = int(time.time() - float(start))
    except Exception:
        return "--:--"
    if secs < 0:
        secs = 0
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def marquee(text, width, pos):
    # Κυλιόμενο κείμενο αν δεν χωράει (αλλιώς ως έχει)
    if len(text) <= width:
        return text
    s = text + "   "
    pos = pos % len(s)
    return (s + s)[pos:pos + width]


def main():
    from luma.core.render import canvas
    from PIL import ImageFont

    device = get_device(port=4)        # Οθόνη 2 (game) -> /dev/i2c-4
    font = ImageFont.load_default()

    aperture_splash(device, font, hold=10.0)

    scroll = 0
    while True:
        d = read_status()
        playing = bool(d.get("game"))

        with canvas(device) as draw:
            if not playing:
                # Καμία ενεργή παρτίδα -> δείχνει το aperture logo
                draw_aperture(draw, 64, 32, 28)
            else:
                game = d.get("game", "?")
                system = d.get("system", "?")
                core = d.get("core", "?")
                fps = d.get("fps", "--")
                target = d.get("target", "--")
                status = d.get("status", "PLAYING").upper()
                play = fmt_play(d.get("start"))

                # Header: κατάσταση αριστερά + ώρα πάνω δεξιά
                draw.text((4, 2), status[:14], font=font, fill="white")
                clock = time.strftime("%H:%M")
                draw.text((124 - len(clock) * 6, 2), clock,
                          font=font, fill="white")
                draw.line((4, 12, 123, 12), fill="white")

                # Όνομα παιχνιδιού (marquee αν μακρύ)
                draw.text((4, 16), marquee(game, 20, scroll),
                          font=font, fill="white")
                # Σύστημα / core
                draw.text((4, 28), f"{system} / {core}"[:20],
                          font=font, fill="white")
                # Play time
                draw.text((4, 40), f"PLAY  {play}", font=font, fill="white")
                # FPS current / target + μπάρα
                draw.text((4, 52), f"FPS {fps}/{target}", font=font, fill="white")
                try:
                    pct = float(fps) / float(target) * 100.0
                except Exception:
                    pct = 0.0
                draw_bar(draw, 70, 53, 52, 6, pct)

        scroll += 1
        time.sleep(0.4)


if __name__ == "__main__":
    main()
