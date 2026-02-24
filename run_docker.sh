#!/bin/bash

# Build the docker image
echo "[*] Building Docker Image..."
docker build -t buddy-bot .

# Run the docker container
# Crucial: Needs --cap-add=NET_ADMIN and --device=/dev/net/tun for OpenVPN to work!
echo "[*] Running Buddy Bot Container..."
docker run --rm -it \
    --cap-add=NET_ADMIN \
    --device=/dev/net/tun \
    --name buddy-bot-run \
    buddy-bot "$@"

# The container will exit with 0 if successful, or 1 if it fails
exit_code=$?
echo "[*] Container finished with exit code: $exit_code"
exit $exit_code
