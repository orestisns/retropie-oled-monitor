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

Run on PC (simulation):
    python game_stats.py --emulate
Run on Pi:
    python3 game_stats.py
"""
import os, time, json

# Reuse the drawing helpers from screen 1
from oled_stats import get_device, draw_aperture, pixel_reveal

STATUS_FILE = os.environ.get(
    "GAME_STATUS_FILE",
    "game_status.txt" if os.name == "nt" else "/tmp/game_status",
)

# Total play time per game (survives reboot)
PLAYTIMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "playtimes.json")


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


def stats_loop(device, font):
    # Only the live game stats (no splash)
    from luma.core.render import canvas

    totals = load_totals()      # {game: total seconds}
    active_game = None           # which game we are currently counting
    active_start = None          # epoch start of current session
    scroll = 0

    while True:
        d = read_status()
        playing = bool(d.get("game"))
        now = time.time()

        if playing:
            game = d.get("game", "?")
            try:
                start = float(d.get("start", now))
            except Exception:
                start = now
            if game != active_game:
                # game changed -> commit the previous session
                if active_game is not None:
                    totals[active_game] = totals.get(active_game, 0) + (now - active_start)
                    save_totals(totals)
                active_game, active_start = game, start
            session = now - active_start
            total_secs = totals.get(game, 0) + session
        else:
            # game ended -> commit the session that just closed
            if active_game is not None:
                totals[active_game] = totals.get(active_game, 0) + (now - active_start)
                save_totals(totals)
                active_game = active_start = None

        with canvas(device) as draw:
            if not playing:
                draw_aperture(draw, 64, 32, 28.5)
            else:
                system = d.get("system", "?")
                core = d.get("core", "?")
                status = d.get("status", "PLAYING").upper()

                # Header: status on the left + clock on the right
                draw.text((4, 2), status[:14], font=font, fill="white")
                clock = time.strftime("%H:%M")
                draw.text((124 - len(clock) * 6, 2), clock,
                          font=font, fill="white")
                draw.line((4, 12, 123, 12), fill="white")

                # Game name (marquee if long)
                draw.text((4, 16), marquee(game, 20, scroll),
                          font=font, fill="white")
                # System / core
                draw.text((4, 28), f"{system} / {core}"[:20],
                          font=font, fill="white")
                # Current session time
                draw.text((4, 40), f"PLAY  {fmt_play(active_start)}",
                          font=font, fill="white")
                # Total time (all sessions)
                draw.text((4, 52), f"TOTAL {fmt_hms(total_secs)}",
                          font=font, fill="white")

        scroll += 1
        time.sleep(0.4)


def run(device, font):
    # Aperture splash -> live game stats (standalone)
    aperture_splash(device, font, hold=10.0)
    stats_loop(device, font)


def main():
    from PIL import ImageFont
    device = get_device(port=4)        # Screen 2 (game) -> /dev/i2c-4
    run(device, ImageFont.load_default())


if __name__ == "__main__":
    main()
