#!/usr/bin/env python3
"""
RetroPie OLED Monitor - drives BOTH displays with a synchronized flow.

  Screen 1 (system) -> I2C bus 3  (GPIO23/24)
  Screen 2 (game)   -> I2C bus 4  (GPIO22/27)

Startup flow:
  1) Screen 1: boot sequence   (screen 2 blank)
  2) Both: logo with pixel-reveal animation (simultaneously)
  3) Both: live stats          (simultaneously, forever)

Run on the Pi:
    python3 monitor.py
"""
import os
import threading
import traceback
from PIL import ImageFont
from luma.core.render import canvas

import oled_stats
import game_stats


def _blank(device):
    with canvas(device):
        pass


def _guard(fn):
    # If a thread crashes, exit the whole process so systemd restarts it
    # (otherwise one screen would silently stay dead).
    def wrapped(*args):
        try:
            fn(*args)
        except Exception:
            traceback.print_exc()
            os._exit(1)
    return wrapped


def _both(target_a, args_a, target_b, args_b):
    ta = threading.Thread(target=_guard(target_a), args=args_a, daemon=True)
    tb = threading.Thread(target=_guard(target_b), args=args_b, daemon=True)
    ta.start()
    tb.start()
    ta.join()
    tb.join()


def main():
    font = ImageFont.load_default()
    dev_system = oled_stats.get_device(port=3)      # /dev/i2c-3
    dev_game = oled_stats.get_device(port=4)        # /dev/i2c-4

    # 1) Boot sequence on screen 1, screen 2 blank
    _blank(dev_game)
    oled_stats.boot_sequence(dev_system, font)

    # 2) Logo with animation on both, simultaneously
    _both(
        oled_stats.splash, (dev_system, font, 5.0),
        game_stats.aperture_splash, (dev_game, font, 5.0),
    )

    # 3) Live stats on both, simultaneously (forever)
    _both(
        oled_stats.stats_loop, (dev_system, font),
        game_stats.stats_loop, (dev_game, font),
    )


if __name__ == "__main__":
    main()
