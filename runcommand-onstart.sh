#!/bin/bash
# RetroPie hook: writes the game state for the OLED game stats (screen 2).
# RetroPie calls this script automatically when a game starts.
#
# Arguments from runcommand:
#   $1 = system     (e.g. nes, snes, psx)
#   $2 = emulator   (e.g. lr-fceumm, pcsx_rearmed)
#   $3 = rom path   (full path of the ROM)
#   $4 = commandline
#
# Install: copy it as
#   /opt/retropie/configs/all/runcommand-onstart.sh
# and make it executable:  chmod +x runcommand-onstart.sh

SYSTEM="$1"
EMULATOR="$2"
ROMPATH="$3"

STATUS_FILE="/tmp/game_status"

# Game name: filename without extension
GAME="$(basename "$ROMPATH")"
GAME="${GAME%.*}"

# Core: strip the "lr-" prefix (libretro)
CORE="${EMULATOR#lr-}"

{
  echo "game=$GAME"
  echo "system=$SYSTEM"
  echo "core=$CORE"
  echo "status=PLAYING"
  echo "target=60"
  echo "start=$(date +%s)"
} > "$STATUS_FILE"
