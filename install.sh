#!/usr/bin/env bash
#
# RetroPie OLED Monitor - installer (no apt, EOL-friendly)
# Runs each step separately, showing what it does and any errors.
#
# Usage (NOT with sudo):
#   cd ~/retropie-oled-monitor
#   chmod +x install.sh
#   ./install.sh
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

echo -e "${BOLD}RetroPie OLED Monitor - Installer (no apt)${NC}"
echo "Project folder: $SCRIPT_DIR"

# --- Check: not as root ---
if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    fail "Do not run with sudo. Just run: ./install.sh"
    exit 1
fi

# --- Step 1: Enable I2C ---
step "1/5  Enable I2C"
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_i2c 0 && ok "I2C enabled" || warn "raspi-config returned an error"
else
    warn "raspi-config not found - make sure I2C is enabled manually"
fi

# --- Step 2: Two software I2C buses in config.txt ---
step "2/5  Create software I2C buses (bus 3 & 4)"
CONFIG=/boot/firmware/config.txt
[ -f "$CONFIG" ] || CONFIG=/boot/config.txt
info "File: $CONFIG"
if [ ! -f "$CONFIG" ]; then
    fail "config.txt not found"
else
    if grep -q "i2c_gpio_sda=23" "$CONFIG"; then
        info "bus 3 already present - skipped"
    else
        echo "dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24" | sudo tee -a "$CONFIG" >/dev/null \
            && ok "Added bus 3 (GPIO23/24)"
    fi
    if grep -q "i2c_gpio_sda=22" "$CONFIG"; then
        info "bus 4 already present - skipped"
    else
        echo "dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27" | sudo tee -a "$CONFIG" >/dev/null \
            && ok "Added bus 4 (GPIO22/27)"
    fi
fi

# --- Step 3: Ensure pip (no apt) ---
step "3/5  Ensure pip is available"
if python3 -m pip --version >/dev/null 2>&1; then
    ok "pip already present: $(python3 -m pip --version)"
else
    info "Bootstrapping pip via ensurepip..."
    python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    if ! python3 -m pip --version >/dev/null 2>&1; then
        info "ensurepip unavailable - trying get-pip (version-matched for EOL Python)..."
        PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "https://bootstrap.pypa.io/pip/$PYV/get-pip.py" -o /tmp/get-pip.py \
              || curl -fsSL "https://bootstrap.pypa.io/get-pip.py" -o /tmp/get-pip.py
        else
            wget -qO /tmp/get-pip.py "https://bootstrap.pypa.io/pip/$PYV/get-pip.py" \
              || wget -qO /tmp/get-pip.py "https://bootstrap.pypa.io/get-pip.py"
        fi
        python3 /tmp/get-pip.py --user >/dev/null 2>&1 || true
    fi
    if python3 -m pip --version >/dev/null 2>&1; then
        ok "pip installed: $(python3 -m pip --version)"
    else
        fail "Could not install pip (check internet connection)"
    fi
fi

# --- Step 4: Python libraries ---
step "4/5  Python libraries (luma.oled, pillow, psutil)"
info "Using prebuilt wheels (piwheels); pillow<10 for Python 3.7 (Buster) compatibility"
# --prefer-binary: never compile from source
# piwheels: official Raspberry Pi wheel host (works on EOL Buster/py3.7)
# pillow<10: Pillow 10+ dropped Python 3.7
PIPW="--extra-index-url https://www.piwheels.org/simple"
if python3 -m pip install --user --prefer-binary $PIPW "pillow<10" luma.oled psutil; then
    if python3 -c "import PIL, psutil, luma.oled" >/dev/null 2>&1; then
        ok "Python libraries installed & importable"
    else
        fail "Installed but not importable - check pip output above"
    fi
else
    fail "pip install failed (check internet / piwheels)"
fi

# --- Step 5a: runcommand hooks (game stats) ---
step "5/5  Install hooks + autostart"
HOOKDIR=/opt/retropie/configs/all
if [ ! -d "$HOOKDIR" ]; then
    fail "$HOOKDIR not found - does not look like RetroPie"
else
    if sudo cp "$SCRIPT_DIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onstart.sh" \
       && sudo cp "$SCRIPT_DIR/runcommand-onend.sh" "$HOOKDIR/runcommand-onend.sh" \
       && sudo chmod +x "$HOOKDIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onend.sh"; then
        ok "Game hooks installed in $HOOKDIR"
    else
        fail "Failed to copy hooks"
    fi
fi

# --- Step 5b: systemd autostart ---
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
echo "Next steps:"
echo "  1) Wire the 2 displays (see README)"
echo "  2) Reboot:   sudo reboot"
echo "  3) After reboot, verify:"
echo "       ls /dev/i2c-3 /dev/i2c-4   (both should exist)"
echo "       systemctl status retropie-oled-monitor.service"
echo
