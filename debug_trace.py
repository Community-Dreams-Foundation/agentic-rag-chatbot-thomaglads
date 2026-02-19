import traceback
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.agent import ComplianceAgent
    print("Success")
except Exception as e:
    with open("traceback.txt", "w") as f:
        traceback.print_exc(file=f)
    print(f"Failed - {e} - check traceback.txt")
