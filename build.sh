#!/bin/bash

# Build OpenSBI firmware
CROSS_COMPILE=riscv64-unknown-linux-gnu- make PLATFORM=generic -j

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Get git SHA for image header
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "Git SHA: $GIT_SHA"

# Add image header to fw_jump.bin
echo "Adding image header to fw_jump.bin..."

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install ecdsa
else
    source venv/bin/activate
fi

# Generate fw_jump.img with image header
python tool/patch_image_header.py build/platform/generic/firmware/fw_jump.bin \
    --add-header \
    -o build/platform/generic/firmware/fw_jump.img \
    --entrypoint 0x40000000 \
    --git-sha "$GIT_SHA" \
    -k tool/key/ec-secp256k1-private.pem

if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
else
    echo "Failed to generate fw_jump.img"
    exit 1
fi