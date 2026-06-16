#!/usr/bin/env python3
"""
RetroPie OLED Monitor — οδηγεί ΚΑΙ τις δύο οθόνες με συγχρονισμένη ροή.

  Οθόνη 1 (system) -> I2C bus 3  (GPIO23/24)
  Οθόνη 2 (game)   -> I2C bus 4  (GPIO22/27)

Ροή στο ξεκίνημα:
  1) Screen 1: boot sequence   (screen 2 κενή)
  2) Και οι δύο: logo με pixel-reveal animation (ταυτόχρονα)
  3) Και οι δύο: live stats     (ταυτόχρονα, για πάντα)

Τρέξιμο στο Pi:
    python3 monitor.py
"""
import threading
from PIL import ImageFont
from luma.core.render import canvas

import oled_stats
import game_stats


def _blank(device):
    with canvas(device):
        pass


def _both(target_a, args_a, target_b, args_b):
    ta = threading.Thread(target=target_a, args=args_a, daemon=True)
    tb = threading.Thread(target=target_b, args=args_b, daemon=True)
    ta.start()
    tb.start()
    ta.join()
    tb.join()


def main():
    font = ImageFont.load_default()
    dev_system = oled_stats.get_device(port=3)      # /dev/i2c-3
    dev_game = oled_stats.get_device(port=4)        # /dev/i2c-4

    # 1) Boot sequence στην οθόνη 1, η οθόνη 2 κενή
    _blank(dev_game)
    oled_stats.boot_sequence(dev_system, font)

    # 2) Logo με animation και στις δύο ταυτόχρονα
    _both(
        oled_stats.splash, (dev_system, font, 5.0),
        game_stats.aperture_splash, (dev_game, font, 5.0),
    )

    # 3) Live stats και στις δύο ταυτόχρονα (ατέρμονα)
    _both(
        oled_stats.stats_loop, (dev_system, font),
        game_stats.stats_loop, (dev_game, font),
    )


if __name__ == "__main__":
    main()
