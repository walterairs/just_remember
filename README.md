# Just Remember - Japanese Grammar SRS

A spaced repetition system (SRS) for learning Japanese grammar, inspired by WaniKani's review system.

## Features

- **Typed Answer System**: Type your answers instead of just rating yourself
  - Fuzzy matching for forgiving answer checking (75% similarity threshold)
  - Accepts variations and partial matches
  - Automatic feedback with match percentage

- **Spaced Repetition System**: Progress through grammar points using an SRS system with stages:
  - Apprentice I-IV (4h, 8h, 1d, 2d intervals)
  - Guru I-II (1w, 2w intervals)  
  - Master (1 month interval)
  - Enlightened (4 months interval)
  - Burned (no more reviews)

- **Grammar Database**: Store and manage Japanese grammar entries with:
  - Grammar patterns and readings
  - Usage explanations
  - English meanings
  - Japanese and English example sentences
  - Notes and additional information
  - Learning progress tracking

- **Review Interface**: Clean PyQt6-based GUI for practicing grammar
  - Type answers in English for grammar meanings
  - Intelligent fuzzy matching accepts close answers
  - Show full answer details on demand
  - Track review statistics

- **Progress Tracking**: Monitor your learning with:
  - SRS stage distribution visualization
  - Overall accuracy statistics
  - Due review counts
  - Complete grammar entry listing

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python src/main.py
   ```

## Usage

### Importing Grammar Data

1. Click "Import Grammar File" in the application
2. Select your TSV grammar file (like the included `n3_grammar.txt`)
3. Grammar entries will be imported and immediately available for review

### Reviewing Grammar

1. Click "Start Review Session" to begin reviewing due items
2. Read the grammar pattern and usage
3. Type what you think the meaning is in English
4. Press Enter or click "Check Answer" to see if you're correct
5. Use "Show Full Answer" to see examples and notes
6. Click "Next" to continue to the next item

### Answer Matching

The system uses fuzzy matching to be forgiving with answers:
- **75% similarity threshold** for correct answers
- Accepts variations like "is/are/am" for "～ is/am/are ～"
- Matches partial meanings like "too" for "too; also"
- Shows match percentage and feedback

### Tracking Progress

- **Statistics Tab**: View your SRS stage distribution and overall progress
- **All Grammar Tab**: Browse all imported grammar entries and their status
- The main window shows how many reviews are currently due

## File Structure

```
just_remember/
├── src/
│   ├── main.py          # PyQt6 GUI application
│   └── models.py        # Data models and database logic
├── n3_grammar.txt       # Sample N3 grammar data (52 entries)
├── requirements.txt     # Python dependencies  
├── test_models.py       # Test script for models
├── test_answers.py      # Test script for answer matching
├── just_remember.py     # Main launcher script
└── README.md           # This file
```

## Grammar Data Format

The application expects TSV (Tab-Separated Values) files with grammar entries. Each line should contain:

```
grammar	grammar_details	usage	meaning	example1_ja	example1_en	example2_ja	example2_en	note
```

See `n3_grammar.txt` for a complete example with 52 N3-level grammar points.

## SRS Algorithm

The spaced repetition system follows these rules:

- **Correct answer (≥75% match)**: Advance to the next SRS stage
- **Incorrect answer (<75% match)**: Reset to Apprentice I
- **Review intervals**: Increase exponentially through stages
- **Burned items**: No longer appear for review

This ensures you spend more time on difficult grammar while maintaining knowledge of mastered items.

## Development

### Testing the Models

Run the test script to verify the core functionality:

```bash
python test_models.py
```

### Testing Answer Matching

Run the answer matching test to verify fuzzy matching:

```bash
python test_answers.py
```

This tests the fuzzy matching with real grammar examples.

### Requirements

- Python 3.7+
- PyQt6 (for GUI)
- fuzzywuzzy (for answer matching)
- python-Levenshtein (for faster fuzzy matching)
- sqlite3 (included with Python)

## Contributing

Feel free to contribute by:

- Adding more grammar data files
- Improving the fuzzy matching algorithm
- Enhancing the UI/UX
- Adding new features like audio support
- Optimizing the SRS algorithm

## License

This project is open source. Feel free to use and modify as needed for your Japanese learning journey!

## Acknowledgments

- Inspired by WaniKani's excellent SRS system
- Grammar data based on standard N3 JLPT materials
- Built with PyQt6 for cross-platform compatibility
- Uses fuzzywuzzy for intelligent answer matching