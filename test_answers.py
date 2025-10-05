#!/usr/bin/env python3
"""
Test script for the fuzzy answer matching system
Run this after installing dependencies: pip install fuzzywuzzy python-Levenshtein
"""

def test_answer_matching():
    """Test the answer matching logic"""
    try:
        from fuzzywuzzy import fuzz
        
        def prepare_acceptable_answers(meaning):
            """Simulate the _prepare_acceptable_answers method"""
            answers = []
            
            # Add the main meaning
            if meaning:
                answers.append(meaning.lower().strip())
                
            # Add variations and common simplifications
            meaning_lower = meaning.lower()
            
            # Remove common prefixes/suffixes
            simplified = meaning_lower.replace("～ is", "").replace("～ am", "").replace("～ are", "")
            simplified = simplified.replace("～", "").strip()
            if simplified and simplified not in answers:
                answers.append(simplified)
                
            # Split on common separators and add individual meanings
            for separator in [",", ";", ".", "!", "?"]:
                if separator in meaning_lower:
                    parts = [part.strip() for part in meaning_lower.split(separator) if part.strip()]
                    for part in parts:
                        clean_part = part.replace("～", "").strip()
                        if clean_part and len(clean_part) > 2 and clean_part not in answers:
                            answers.append(clean_part)
            
            return answers
        
        def check_answer(user_answer, meaning):
            """Check if user answer matches the meaning"""
            acceptable_answers = prepare_acceptable_answers(meaning)
            user_answer = user_answer.strip().lower()
            
            best_match_score = 0
            best_match = ""
            
            for acceptable in acceptable_answers:
                ratio_score = fuzz.ratio(user_answer, acceptable)
                partial_score = fuzz.partial_ratio(user_answer, acceptable)
                token_score = fuzz.token_sort_ratio(user_answer, acceptable)
                
                best_score = max(ratio_score, partial_score, token_score)
                
                if best_score > best_match_score:
                    best_match_score = best_score
                    best_match = acceptable
            
            is_correct = best_match_score >= 75
            return is_correct, best_match_score, best_match, acceptable_answers
        
        # Test cases with grammar from the N3 file
        test_cases = [
            # Grammar pattern, user input, expected meaning
            ("～です", "is", "～ is/am/are ～"),
            ("～です", "are", "～ is/am/are ～"),
            ("～です", "am", "～ is/am/are ～"),
            ("も", "too", "too; also"),
            ("も", "also", "too; also"),
            ("で", "place", "marks the place where an action takes place. Marks the means by which you do something."),
            ("で", "means", "marks the place where an action takes place. Marks the means by which you do something."),
            ("～に/へ行く", "go to", "go to ～ come to ～"),
            ("～に/へ行く", "come to", "go to ～ come to ～"),
            ("Timeに", "at", "at, during, etc."),
            ("Timeに", "during", "at, during, etc."),
        ]
        
        print("Testing Answer Matching System")
        print("=" * 50)
        
        correct_count = 0
        total_count = len(test_cases)
        
        for grammar, user_input, meaning in test_cases:
            is_correct, score, best_match, acceptable = check_answer(user_input, meaning)
            
            result = "✓ PASS" if is_correct else "✗ FAIL"
            print(f"{result} - '{grammar}': '{user_input}' -> {score}% match")
            print(f"    Expected: {meaning}")
            print(f"    Best match: {best_match}")
            print(f"    Acceptable answers: {acceptable}")
            print()
            
            if is_correct:
                correct_count += 1
        
        print(f"Results: {correct_count}/{total_count} tests passed ({correct_count/total_count*100:.1f}%)")
        
        if correct_count >= total_count * 0.8:  # 80% pass rate
            print("✓ Answer matching system is working well!")
        else:
            print("⚠ Answer matching may need tuning")
            
    except ImportError:
        print("Dependencies not installed. Run:")
        print("pip install fuzzywuzzy python-Levenshtein")

if __name__ == "__main__":
    test_answer_matching()