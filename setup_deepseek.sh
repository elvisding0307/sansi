#!/bin/bash
# ============================================================================
# SanSi - Environment Setup
# ============================================================================
# Usage:
#   1. Copy .env.example to .env and fill in your API keys
#   2. Source this file or the .env directly:
#      source .env
#      # or
#      source setup_deepseek.sh
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  .env file not found. Create one from the template:"
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your API keys"
fi
