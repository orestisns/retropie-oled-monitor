#!/bin/bash
# RetroPie hook: clears the state when a game exits.
# RetroPie calls it automatically as soon as you exit a game.
# Without the file, screen 2 shows the aperture logo (idle).
#
# Install: copy it as
#   /opt/retropie/configs/all/runcommand-onend.sh
# and make it executable:  chmod +x runcommand-onend.sh

rm -f /tmp/game_status
