#!/usr/bin/env python3
"""
OLED Game / Emulation Stats (128x64, SSD1306) - Screen 2.

Reads the game state from a key=value file:
    game=Super Mario Bros
    system=NES
    core=fceumm
    fps=59
    target=60
    status=PLAYING
    start=<epoch seconds>

On the Pi the file is written by runcommand-onstart.sh (see notes).

One button toggles the page: GPIO6 (pin 31) -> GND. Press = PAGE 2, press
again = back to the stats. On PC (--emulate) the page auto-toggles for preview.

Run on PC (simulation):
    python game_stats.py --emulate
Run on Pi:
    python3 game_stats.py
"""
import os, time, json

# Reuse the drawing helpers + Toggle from screen 1
from oled_stats import (get_device, draw_aperture, pixel_reveal, ctext,
                        Toggle, screen_off, screen_on)

STATUS_FILE = os.environ.get(
    "GAME_STATUS_FILE",
    "game_status.txt" if os.name == "nt" else "/tmp/game_status",
)

# Total play time per game (survives reboot)
PLAYTIMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "playtimes.json")

GAME_BUTTON_PIN = 6   # BCM GPIO6 = physical pin 31 -> screen 2 (game)


def load_totals():
    try:
        with open(PLAYTIMES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_totals(totals):
    try:
        with open(PLAYTIMES_FILE, "w") as f:
            json.dump(totals, f)
    except Exception:
        pass


def fmt_hms(secs):
    secs = max(0, int(secs))
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def aperture_splash(device, font, hold=10.0):
    # Aperture logo with pixel-reveal animation (shared function)
    pixel_reveal(device, lambda d: draw_aperture(d, 64, 32, 28.5), hold=hold)


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
    # Scrolling text if it does not fit (otherwise as-is)
    if len(text) <= width:
        return text
    s = text + "   "
    pos = pos % len(s)
    return (s + s)[pos:pos + width]


def draw_game_page(draw, font, d, active_start, total_secs, scroll):
    # Page 0: live game stats (or aperture logo when idle)
    if not d.get("game"):
        draw_aperture(draw, 64, 32, 28.5)
        return
    game = d.get("game", "?")
    system = d.get("system", "?")
    core = d.get("core", "?")
    status = d.get("status", "PLAYING").upper()

    draw.text((4, 2), status[:14], font=font, fill="white")
    clock = time.strftime("%H:%M")
    draw.text((124 - len(clock) * 6, 2), clock, font=font, fill="white")
    draw.line((4, 12, 123, 12), fill="white")
    draw.text((4, 16), marquee(game, 20, scroll), font=font, fill="white")
    draw.text((4, 28), f"{system} / {core}"[:20], font=font, fill="white")
    draw.text((4, 40), f"PLAY  {fmt_play(active_start)}", font=font, fill="white")
    draw.text((4, 52), f"TOTAL {fmt_hms(total_secs)}", font=font, fill="white")


def stats_loop(device, font, pager=None):
    # Live game stats with page switching (no splash)
    from luma.core.render import canvas

    if pager is None:
        pager = Toggle(GAME_BUTTON_PIN)
    totals = load_totals()
    active_game = None
    active_start = None
    scroll = 0
    off = False
    last_data = 0.0
    last_page = -1
    d = {}
    total_secs = 0

    while True:
        pager.poll()
        if not pager.power:            # long-press turned the screen off
            if not off:
                screen_off(device)
                off = True
            last_page = -1             # force redraw when turned back on
            time.sleep(0.1)
            continue
        if off:
            screen_on(device)
            off = False
            last_page = -1

        now = time.time()
        data_due = now - last_data >= 0.4
        if data_due:
            d = read_status()
            playing = bool(d.get("game"))
            total_secs = 0
            if playing:
                game = d.get("game", "?")
                try:
                    start = float(d.get("start", now))
                except Exception:
                    start = now
                if game != active_game:
                    if active_game is not None:
                        totals[active_game] = totals.get(active_game, 0) + (now - active_start)
                        save_totals(totals)
                    active_game, active_start = game, start
                total_secs = totals.get(game, 0) + (now - active_start)
            else:
                if active_game is not None:
                    totals[active_game] = totals.get(active_game, 0) + (now - active_start)
                    save_totals(totals)
                    active_game = active_start = None
            scroll += 1
            last_data = now

        # Re-render on a data tick OR immediately when the page changed
        if data_due or pager.page != last_page:
            with canvas(device) as draw:
                if pager.page == 1:
                    ctext(draw, font, 26, "PAGE 2")
                else:
                    draw_game_page(draw, font, d, active_start, total_secs, scroll)
            last_page = pager.page

        time.sleep(0.1)


def run(device, font, pager=None):
    # Aperture splash -> live game stats (standalone)
    aperture_splash(device, font, hold=10.0)
    stats_loop(device, font, pager)


def main():
    from PIL import ImageFont
    device = get_device(port=4)        # Screen 2 (game) -> /dev/i2c-4
    run(device, ImageFont.load_default())


if __name__ == "__main__":
    main()
