#!/usr/bin/env bash
#
# RetroPie OLED Monitor - installer (APT method / backup for EOL systems)
#
# Use this if the default ./install.sh (piwheels) fails to find wheels
# (e.g. under QEMU). It:
#   1) repoints apt to the archive (safe, read-only) and disables the
#      expired Release date check,
#   2) installs build tools via apt (so pip CAN compile Pillow/psutil),
#   3) installs the Python libs via pip.
#
# Usage (NOT with sudo):
#   cd ~/retropie-oled-monitor
#   chmod +x install-apt.sh
#   ./install-apt.sh
#
set -u

GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; CYA='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
step()  { echo; echo -e "${CYA}${BOLD}==> $1${NC}"; }
info()  { echo -e "    $1"; }
ok()    { echo -e "    ${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "    ${YEL}[WARN]${NC} $1"; WARN_COUNT=$((WARN_COUNT+1)); }
fail()  { echo -e "    ${RED}[ERROR]${NC} $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

WARN_COUNT=0
FAIL_COUNT=0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BOLD}RetroPie OLED Monitor - Installer (APT / archive)${NC}"
echo "Project folder: $SCRIPT_DIR"

if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    fail "Do not run with sudo. Just run: ./install-apt.sh"
    exit 1
fi

# Codename (buster, etc.)
CODENAME="buster"
[ -r /etc/os-release ] && CODENAME="$(. /etc/os-release; echo "${VERSION_CODENAME:-buster}")"

url_ok() { curl -sI "$1" 2>/dev/null | head -1 | grep -q "200"; }

# --- Step 1: Repoint apt sources to a working archive ---
step "1/6  Fix apt sources to archive ($CODENAME)"
RASPBIAN=""
for h in http://legacy.raspbian.org/raspbian \
         http://raspbian.raspberrypi.org/raspbian \
         http://mirrordirector.raspbian.org/raspbian; do
    if url_ok "$h/dists/$CODENAME/Release"; then RASPBIAN="$h"; break; fi
done
FOUNDATION=""
for h in http://archive.raspberrypi.org/debian \
         http://legacy.raspberrypi.org/debian; do
    if url_ok "$h/dists/$CODENAME/Release"; then FOUNDATION="$h"; break; fi
done

if [ -n "$RASPBIAN" ]; then
    sudo cp /etc/apt/sources.list "/etc/apt/sources.list.bak.$(date +%s)" 2>/dev/null
    echo "deb $RASPBIAN $CODENAME main contrib non-free rpi" | sudo tee /etc/apt/sources.list >/dev/null
    ok "raspbian -> $RASPBIAN"
else
    warn "No working raspbian archive found - leaving /etc/apt/sources.list unchanged"
fi
if [ -n "$FOUNDATION" ]; then
    echo "deb $FOUNDATION $CODENAME main" | sudo tee /etc/apt/sources.list.d/raspi.list >/dev/null
    ok "foundation -> $FOUNDATION"
else
    warn "No working foundation archive found - leaving raspi.list unchanged"
fi
echo 'Acquire::Check-Valid-Until "false";' | sudo tee /etc/apt/apt.conf.d/10no-check-valid-until >/dev/null
info "Disabled expired Release date check"

# --- Step 2: apt update ---
step "2/6  apt update"
if sudo apt-get update -o Acquire::Check-Valid-Until=false; then
    ok "Package lists updated"
else
    fail "apt update failed (archive URL may be wrong - check Step 1 output)"
fi

# --- Step 3: build tools + system tools via apt ---
step "3/6  apt install build tools (so pip can compile Pillow/psutil)"
if sudo apt-get install -y python3-pip python3-dev gcc libjpeg-dev zlib1g-dev i2c-tools git; then
    ok "Tools installed"
else
    fail "apt install failed"
fi

# --- Step 4: Enable I2C + software buses ---
step "4/6  Enable I2C + create software buses (bus 3 & 4)"
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_i2c 0 && ok "I2C enabled" || warn "raspi-config error"
else
    warn "raspi-config not found - enable I2C manually"
fi
CONFIG=/boot/firmware/config.txt
[ -f "$CONFIG" ] || CONFIG=/boot/config.txt
if [ -f "$CONFIG" ]; then
    grep -q "i2c_gpio_sda=23" "$CONFIG" || echo "dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24" | sudo tee -a "$CONFIG" >/dev/null
    grep -q "i2c_gpio_sda=22" "$CONFIG" || echo "dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27" | sudo tee -a "$CONFIG" >/dev/null
    ok "config.txt updated ($CONFIG)"
else
    fail "config.txt not found"
fi

# --- Step 5: Python libraries via pip (build deps now present) ---
step "5/6  Python libraries (pillow<10, luma.oled, psutil)"
if python3 -m pip install --user --prefer-binary "pillow<10" luma.oled psutil; then
    if python3 -c "import PIL, psutil, luma.oled" >/dev/null 2>&1; then
        ok "Python libraries installed & importable"
    else
        fail "Installed but not importable - check pip output above"
    fi
else
    fail "pip install failed"
fi

# --- Step 6: hooks + autostart ---
step "6/6  Install hooks + autostart"
HOOKDIR=/opt/retropie/configs/all
if [ -d "$HOOKDIR" ]; then
    sudo cp "$SCRIPT_DIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onstart.sh" \
      && sudo cp "$SCRIPT_DIR/runcommand-onend.sh" "$HOOKDIR/runcommand-onend.sh" \
      && sudo chmod +x "$HOOKDIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onend.sh" \
      && ok "Game hooks installed" || fail "Failed to copy hooks"
else
    fail "$HOOKDIR not found - does not look like RetroPie"
fi
SVC=/etc/systemd/system/retropie-oled-monitor.service
if sudo cp "$SCRIPT_DIR/retropie-oled-monitor.service" "$SVC" \
   && sudo sed -i "s|/home/pi/retropie-oled-monitor|$SCRIPT_DIR|g; s|^User=pi|User=$USER|" "$SVC" \
   && sudo systemctl daemon-reload \
   && sudo systemctl enable retropie-oled-monitor.service; then
    ok "Service installed & enabled (User=$USER, dir=$SCRIPT_DIR)"
else
    fail "Failed to install service"
fi

# --- Summary ---
echo
echo -e "${BOLD}==================== SUMMARY ====================${NC}"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}All steps completed.${NC} (warnings: $WARN_COUNT)"
else
    echo -e "${RED}Completed with $FAIL_COUNT error(s)${NC} and $WARN_COUNT warning(s) - see above."
fi
echo
echo "Next: wire the displays, then 'sudo reboot'."
echo "Verify: ls /dev/i2c-3 /dev/i2c-4   and   systemctl status retropie-oled-monitor.service"
echo
