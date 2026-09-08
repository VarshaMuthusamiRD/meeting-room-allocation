#!/usr/bin/env python3
"""Single documented entry point (TC5): python run.py <command> [args...]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mrbooking.cli import main

if __name__ == "__main__":
    sys.exit(main())
