#!/usr/bin/env bash
# Install system dependencies for GitHub Actions runners.
# Called from generate.yml. ubuntu-latest includes ffmpeg but fonts-inter requires apt-get.
set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends fonts-inter
