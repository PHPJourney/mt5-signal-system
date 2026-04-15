#!/bin/bash
# MT5 Signal System - macOS Installation Script
# Supports selecting Master, Slave, or Unified components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  MT5 Signal System - Installer"
echo "============================================"
echo ""

# Default installation directory
INSTALL_DIR="/Applications/MT5SignalSystem"

# Check if running as root for /Applications
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Installing to user home directory (need sudo for /Applications)${NC}"
    INSTALL_DIR="$HOME/Applications/MT5SignalSystem"
fi

# Ask for installation directory
read -p "Installation directory [$INSTALL_DIR]: " user_dir
if [ -n "$user_dir" ]; then
    INSTALL_DIR="$user_dir"
fi

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Component selection
echo ""
echo "Select components to install:"
echo "  1) Master Panel (主信号管理面板)"
echo "  2) Slave Panel (从信号管理面板)"
echo "  3) Unified Manager (统一管理平台)"
echo "  4) All components"
echo ""

read -p "Enter choice (1/2/3/4, default 4): " choice
choice=${choice:-4}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"

# Check if dist directory exists
if [ ! -d "$DIST_DIR" ]; then
    echo -e "${RED}Error: dist directory not found. Please build first.${NC}"
    exit 1
fi

# Install selected components
install_component() {
    local name=$1
    local src=$2

    if [ -f "$src" ] || [ -d "$src" ]; then
        cp -R "$src" "$INSTALL_DIR/"
        echo -e "${GREEN}✓ Installed: $name${NC}"
    else
        echo -e "${YELLOW}⚠ Skipped (not found): $name${NC}"
    fi
}

case $choice in
    1)
        echo ""
        echo "Installing Master Panel..."
        install_component "Master Panel" "$DIST_DIR/MT5_Master_Panel.app"
        ;;
    2)
        echo ""
        echo "Installing Slave Panel..."
        install_component "Slave Panel" "$DIST_DIR/MT5_Slave_Panel.app"
        ;;
    3)
        echo ""
        echo "Installing Unified Manager..."
        install_component "Unified Manager" "$DIST_DIR/MT5_Unified_Manager.app"
        ;;
    4|*)
        echo ""
        echo "Installing all components..."
        install_component "Master Panel" "$DIST_DIR/MT5_Master_Panel.app"
        install_component "Slave Panel" "$DIST_DIR/MT5_Slave_Panel.app"
        install_component "Unified Manager" "$DIST_DIR/MT5_Unified_Manager.app"
        ;;
esac

# Copy config directory if exists
if [ -d "$SCRIPT_DIR/config" ]; then
    mkdir -p "$INSTALL_DIR/config"
    cp -R "$SCRIPT_DIR/config/"* "$INSTALL_DIR/config/" 2>/dev/null || true
    echo -e "${GREEN}✓ Installed: Configuration files${NC}"
fi

# Copy documentation if exists
for doc in README.md QUICKSTART.md; do
    if [ -f "$SCRIPT_DIR/$doc" ]; then
        cp "$SCRIPT_DIR/$doc" "$INSTALL_DIR/"
        echo -e "${GREEN}✓ Installed: $doc${NC}"
    fi
done

# Create launch scripts
cat > "$INSTALLDIR/start_master.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
open MT5_Master_Panel.app
EOF
chmod +x "$INSTALL_DIR/start_master.sh" 2>/dev/null || true

cat > "$INSTALL_DIR/start_slave.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
open MT5_Slave_Panel.app
EOF
chmod +x "$INSTALL_DIR/start_slave.sh" 2>/dev/null || true

cat > "$INSTALL_DIR/start_unified.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
open MT5_Unified_Manager.app
EOF
chmod +x "$INSTALL_DIR/start_unified.sh" 2>/dev/null || true

echo ""
echo "============================================"
echo -e "${GREEN}Installation complete!${NC}"
echo "============================================"
echo ""
echo "Installed to: $INSTALL_DIR"
echo ""
echo "To launch:"
if [ "$choice" = "1" ] || [ "$choice" = "4" ]; then
    echo "  Master Panel: open $INSTALL_DIR/MT5_Master_Panel.app"
fi
if [ "$choice" = "2" ] || [ "$choice" = "4" ]; then
    echo "  Slave Panel: open $INSTALL_DIR/MT5_Slave_Panel.app"
fi
if [ "$choice" = "3" ] || [ "$choice" = "4" ]; then
    echo "  Unified Manager: open $INSTALL_DIR/MT5_Unified_Manager.app"
fi
echo ""
