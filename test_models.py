#!/usr/bin/env python3
"""
Test script for the grammar models and database functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models import GrammarEntry, GrammarDatabase, SRSManager, SRSStage, parse_grammar_file
from datetime import datetime

def test_models():
    """Test the models and database functionality"""
    print("Testing Just Remember Grammar SRS System")
    print("=" * 50)
    
    # Create test database
    db = GrammarDatabase("test_grammar.db")
    
    # Test creating a grammar entry
    entry = GrammarEntry(
        grammar="～です",
        usage="～が～です。 ～は～です。",
        meaning="～ is/am/are ～",
        example1_ja="これは私の携帯です。",
        example1_en="This is my phone.",
        example2_ja="彼のお姉さんは20歳です。",
        example2_en="His older sister is 20 years old.",
        learned_date=datetime.now(),
        next_review=SRSManager.calculate_next_review(SRSStage.APPRENTICE_1)
    )
    
    # Add entry to database
    entry_id = db.add_entry(entry)
    print(f"Added entry with ID: {entry_id}")
    
    # Retrieve and display entry
    retrieved_entry = db.get_entry(entry_id)
    if retrieved_entry:
        print(f"Retrieved entry: {retrieved_entry.grammar}")
        print(f"Meaning: {retrieved_entry.meaning}")
        print(f"SRS Stage: {retrieved_entry.srs_stage.value}")
    
    # Test SRS progression
    print("\nTesting SRS progression:")
    if retrieved_entry:
        updated_entry = SRSManager.update_progress(retrieved_entry, True)  # Correct answer
        print(f"After correct answer: {updated_entry.srs_stage.value}")
        
        updated_entry = SRSManager.update_progress(updated_entry, False)  # Incorrect answer
        print(f"After incorrect answer: {updated_entry.srs_stage.value}")
    
    # Test importing from file if it exists
    grammar_file = "n3_grammar.txt"
    if os.path.exists(grammar_file):
        print(f"\nImporting from {grammar_file}...")
        try:
            parse_grammar_file(grammar_file, db)
            all_entries = db.get_all_entries()
            print(f"Total entries in database: {len(all_entries)}")
            
            # Show stage distribution
            for stage in SRSStage:
                count = len(db.get_entries_by_stage(stage))
                if count > 0:
                    print(f"{stage.value}: {count} entries")
                    
        except (OSError, ValueError, IndexError) as e:
            print(f"Error importing file: {e}")
    else:
        print(f"\nGrammar file {grammar_file} not found. Create some test entries instead.")
    
    # Test due reviews
    due_reviews = db.get_due_reviews()
    print(f"\nDue reviews: {len(due_reviews)}")
    
    print("\nTest completed successfully!")
    
    # Clean up test database
    if os.path.exists("test_grammar.db"):
        os.remove("test_grammar.db")

if __name__ == "__main__":
    test_models()