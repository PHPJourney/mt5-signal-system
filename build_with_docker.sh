#!/bin/bash
# Docker-based Cross-Compilation for Windows EXE
# This script uses a Docker container to build Windows executables on macOS/Linux

set -e

echo "==============================================="
echo "  MT5 Signal System - Docker EXE Builder"
echo "==============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed!"
    echo "Please install Docker Desktop for Mac:"
    echo "https://docs.docker.com/desktop/install/mac-install/"
    exit 1
fi

echo "[OK] Docker found"
docker --version
echo ""

# Create Dockerfile for Windows build
cat > Dockerfile.windows << 'EOF'
FROM python:3.11-windowsservercore

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir \
    pyinstaller \
    paho-mqtt \
    MetaTrader5

# Build Master Server
RUN pyinstaller --name="MT5_Master_Server" \
    --onedir \
    --console \
    --add-data "config;config" \
    --hidden-import=paho.mqtt.client \
    --hidden-import=MetaTrader5 \
    --hidden-import=common \
    --hidden-import=common.models \
    --hidden-import=common.utils \
    --hidden-import=common.mqtt_client \
    master/signal_sender.py

# Build Slave Server
RUN pyinstaller --name="MT5_Slave_Server" \
    --onedir \
    --console \
    --add-data "config;config" \
    --hidden-import=paho.mqtt.client \
    --hidden-import=MetaTrader5 \
    --hidden-import=common \
    --hidden-import=common.models \
    --hidden-import=common.utils \
    --hidden-import=common.mqtt_client \
    --hidden-import=slave \
    --hidden-import=slave.symbol_mapper \
    --hidden-import=slave.risk_manager \
    slave/signal_receiver.py

# Create release package
RUN mkdir C:\app\dist\MT5_Signal_System_Release && \
    xcopy /E /I C:\app\dist\MT5_Master_Server C:\app\dist\MT5_Signal_System_Release\Master_Server && \
    xcopy /E /I C:\app\dist\MT5_Slave_Server C:\app\dist\MT5_Signal_System_Release\Slave_Server && \
    xcopy /E /I C:\app\config C:\app\dist\MT5_Signal_System_Release\config

CMD ["echo", "Build completed!"]
EOF

echo "[INFO] Building Docker image..."
echo ""

# Build Docker image
docker build -f Dockerfile.windows -t mt5-signal-builder .

echo ""
echo "[OK] Docker image built successfully"
echo ""

# Extract built files
echo "[INFO] Extracting built executables..."
CONTAINER_ID=$(docker create mt5-signal-builder)
docker cp $CONTAINER_ID:/app/dist/MT5_Signal_System_Release ./dist_windows
docker rm $CONTAINER_ID

echo ""
echo "[OK] Executables extracted to: ./dist_windows/"
echo ""

# Cleanup
rm -f Dockerfile.windows

echo "==============================================="
echo "  Build Completed!"
echo "==============================================="
echo ""
echo "Output: dist_windows/MT5_Signal_System_Release/"
echo ""
echo "To distribute:"
echo "1. Zip the dist_windows directory"
echo "2. Share with Windows users"
echo "3. Users just need to extract and run .bat files"
echo ""
