"""Entry point for running Tame-the-Time as a package."""

import sys
import os

# Add parent directory to path so we can import TameTheTime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TameTheTime import main as tame_main

def main():
    """Wrapper function for the main entry point."""
    tame_main()

if __name__ == "__main__":
    main()
