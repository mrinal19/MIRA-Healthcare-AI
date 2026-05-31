#!/bin/bash
# MIRA – One-command startup script
# Usage: ./start.sh
# Usage with AI: ANTHROPIC_API_KEY=sk-ant-xxx ./start.sh

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MIRA – Medical Intelligence Robotic Automation         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is required. Install from https://python.org"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION found"

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ℹ  ANTHROPIC_API_KEY not set — using rule-based health assessment"
  echo "   To enable Claude AI: export ANTHROPIC_API_KEY=sk-ant-your-api-key"
else
  echo "✓ Claude AI API key detected"
fi

echo ""
echo "Starting server on http://localhost:8000 ..."
echo "Press Ctrl+C to stop."
echo ""

# Run from the project root so relative paths work
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python3 backend/server.py
