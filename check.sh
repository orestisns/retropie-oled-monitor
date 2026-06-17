#!/usr/bin/env bash
#
# RetroPie OLED Monitor - dependency checker
# Checks what is already installed so you can skip apt if possible.
#
# Usage:
#   chmod +x check.sh
#   ./check.sh
#
GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; CYA='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC}      $1"; }
miss() { echo -e "  ${RED}[MISSING]${NC} $1"; }

MISSING_BIN=0
MISSING_PY=0

echo -e "${BOLD}RetroPie OLED Monitor - dependency check${NC}"

echo -e "\n${CYA}${BOLD}Binaries${NC}"
for c in git i2cdetect pip3 python3; do
    if command -v "$c" >/dev/null 2>&1; then
        ok "$c  ($(command -v "$c"))"
    else
        miss "$c"
        MISSING_BIN=$((MISSING_BIN+1))
    fi
done

echo -e "\n${CYA}${BOLD}Python modules${NC}"
for m in PIL psutil luma.oled luma.core; do
    if python3 -c "import $m" >/dev/null 2>&1; then
        ok "$m"
    else
        miss "$m"
        MISSING_PY=$((MISSING_PY+1))
    fi
done

echo -e "\n${CYA}${BOLD}Dev libraries (only needed if Pillow must compile)${NC}"
for d in libjpeg-dev zlib1g-dev; do
    if dpkg -s "$d" 2>/dev/null | grep -q "install ok"; then
        ok "$d"
    else
        miss "$d (probably not needed - Pillow usually installs as a wheel)"
    fi
done

echo -e "\n${BOLD}==================== VERDICT ====================${NC}"
if [ "$MISSING_BIN" -eq 0 ] && [ "$MISSING_PY" -eq 0 ]; then
    echo -e "${GREEN}Everything is already installed.${NC}"
    echo "You can SKIP apt entirely. Just install the hooks + service:"
    echo "  - run ./install.sh and ignore step 1 errors, OR"
    echo "  - do steps 6 and 7 from INSTALL.md manually."
elif [ "$MISSING_BIN" -eq 0 ]; then
    echo -e "${YEL}Tools are present, but some Python modules are missing.${NC}"
    echo "No apt needed - just install the Python libraries:"
    echo "  pip3 install luma.oled pillow psutil"
    echo "  (if it complains: add --break-system-packages)"
else
    echo -e "${RED}Some tools are missing.${NC}"
    echo "You need apt for those (git / i2c-tools / python3-pip)."
    echo "If apt gives 404, your RetroPie OS is likely EOL - fix the apt"
    echo "sources first (send the output of: cat /etc/os-release)."
fi
echo
