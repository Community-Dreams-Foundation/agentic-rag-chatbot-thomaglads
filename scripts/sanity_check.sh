#!/bin/bash
# Sanity check script for judges
# Runs make sanity and validates output

set -e

echo "Running Codex sanity check..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Run the sanity check
python3 scripts/sanity_check.py

# Validate output file exists
if [ ! -f "artifacts/sanity_output.json" ]; then
    echo "Error: artifacts/sanity_output.json not found"
    exit 1
fi

echo ""
echo "Sanity check complete!"
echo "Output file: artifacts/sanity_output.json"

# Show summary
python3 -c "
import json
with open('artifacts/sanity_output.json') as f:
    data = json.load(f)
    print(f\"Status: {data.get('status', 'UNKNOWN')}\")
    print(f\"Checks: {len(data.get('checks', {}))}\")
"
