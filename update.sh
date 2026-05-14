#!/usr/bin/env bash
set -e
git pull --recurse-submodules
git submodule update --remote --merge --recursive
docker compose up -d --build
