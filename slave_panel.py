"""
MT5 Signal System - Slave Management Panel Entry Point

This script launches the management panel in Slave mode,
showing only Slave-related features.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run unified manager in slave mode
from mt5_unified_manager import main as unified_main

if __name__ == "__main__":
    # Force slave mode
    sys.argv = [sys.argv[0], '--mode', 'slave']
    unified_main()
