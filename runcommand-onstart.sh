#!/bin/bash
# RetroPie hook: γράφει την κατάσταση παιχνιδιού για τα OLED game stats (screen 2).
# Το RetroPie καλεί αυτό το script αυτόματα όταν ξεκινά ένα παιχνίδι.
#
# Ορίσματα από το runcommand:
#   $1 = system     (π.χ. nes, snes, psx)
#   $2 = emulator   (π.χ. lr-fceumm, pcsx_rearmed)
#   $3 = rom path   (πλήρης διαδρομή του ROM)
#   $4 = commandline
#
# Εγκατάσταση: αντίγραψέ το ως
#   /opt/retropie/configs/all/runcommand-onstart.sh
# και κάνε το εκτελέσιμο:  chmod +x runcommand-onstart.sh

SYSTEM="$1"
EMULATOR="$2"
ROMPATH="$3"

STATUS_FILE="/tmp/game_status"

# Όνομα παιχνιδιού: filename χωρίς κατάληξη
GAME="$(basename "$ROMPATH")"
GAME="${GAME%.*}"

# Core: αφαίρεση προθέματος "lr-" (libretro)
CORE="${EMULATOR#lr-}"

{
  echo "game=$GAME"
  echo "system=$SYSTEM"
  echo "core=$CORE"
  echo "status=PLAYING"
  echo "target=60"
  echo "start=$(date +%s)"
} > "$STATUS_FILE"
