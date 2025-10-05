#!/usr/bin/env python3
"""
Just Remember - Japanese Grammar SRS Application

This is a spaced repetition system (SRS) for learning Japanese grammar,
inspired by WaniKani's review system.

To run the application:
1. Install dependencies: pip install -r requirements.txt
2. Run the GUI application: python src/main.py
3. Or test the models: python test_models.py

Features:
- Import grammar from TSV files
- Spaced repetition system with stages: Apprentice → Guru → Master → Enlightened → Burned
- Review interface for practicing grammar
- Statistics tracking and progress visualization
- SQLite database for persistence
"""

import sys
import os

def main():
    """Main launcher function"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run test mode
        print("Running in test mode...")
        exec(open("test_models.py").read())
    else:
        # Try to run the GUI application
        try:
            import PyQt6
            print("Starting Just Remember GUI application...")
            exec(open("src/main.py").read())
        except ImportError:
            print("PyQt6 not found. Please install dependencies first:")
            print("pip install -r requirements.txt")
            print("\nOr run in test mode: python just_remember.py test")

if __name__ == "__main__":
    main()