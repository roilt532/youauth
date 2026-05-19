#!/usr/bin/env bash
# Install system dependencies for GitHub Actions runners.
# Called from generate.yml.
set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends ffmpeg fonts-inter
