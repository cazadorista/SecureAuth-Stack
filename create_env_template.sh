#!/bin/bash
awk '/^[[:space:]]*#/ {print; next} /=/ {sub(/=.*/, "="); print; next} {print}' .env > .env-template