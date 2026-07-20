#!/bin/bash
# ============================================================================
# SanSi + DeepSeek - Environment Setup
# Run before starting the project:
#   source setup_deepseek.sh
# ============================================================================

# DeepSeek API Configuration
export DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
export DEEPSEEK_MODEL="deepseek-chat"

# These are required by the openai-agents SDK (it reads OPENAI_* env vars internally)
export OPENAI_API_KEY="$DEEPSEEK_API_KEY"
export OPENAI_BASE_URL="$DEEPSEEK_BASE_URL"
export OPENAI_MODEL_NAME="$DEEPSEEK_MODEL"

echo "✅ DeepSeek environment variables set"
echo "   DEEPSEEK_BASE_URL = $DEEPSEEK_BASE_URL"
echo "   DEEPSEEK_MODEL    = $DEEPSEEK_MODEL"
echo ""
echo "⚠️  Make sure to edit this file and replace YOUR_DEEPSEEK_API_KEY with your actual key"
