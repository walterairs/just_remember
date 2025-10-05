from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
import sqlite3

class SRSStage(Enum):
    """Spaced Repetition System stages similar to WaniKani"""
    APPRENTICE_1 = "Apprentice I"
    APPRENTICE_2 = "Apprentice II" 
    APPRENTICE_3 = "Apprentice III"
    APPRENTICE_4 = "Apprentice IV"
    GURU_1 = "Guru I"
    GURU_2 = "Guru II"
    MASTER = "Master"
    ENLIGHTENED = "Enlightened"
    BURNED = "Burned"

class LessonStatus(Enum):
    """Status for lesson management"""
    NOT_STARTED = "Not Started"  # Not yet available for lessons
    AVAILABLE = "Available"      # Available for lessons but not started
    IN_PROGRESS = "In Progress"  # Currently in SRS system

@dataclass
class GrammarEntry:
    """Model for Japanese grammar entries"""
    id: Optional[int] = None
    grammar: str = ""
    grammar_kana: str = ""
    usage: str = ""
    meaning: str = ""
    example1_ja: str = ""
    example1_en: str = ""
    example2_ja: str = ""
    example2_en: str = ""
    note: str = ""
    learned_date: Optional[datetime] = None
    srs_stage: SRSStage = SRSStage.APPRENTICE_1
    lesson_status: LessonStatus = LessonStatus.NOT_STARTED
    next_review: Optional[datetime] = None
    correct_answers: int = 0
    incorrect_answers: int = 0
    last_reviewed: Optional[datetime] = None

class SRSManager:
    """Manages spaced repetition system logic"""
    
    # Time intervals for each SRS stage (in hours)
    INTERVALS = {
        SRSStage.APPRENTICE_1: 4,
        SRSStage.APPRENTICE_2: 8,
        SRSStage.APPRENTICE_3: 24,
        SRSStage.APPRENTICE_4: 48,
        SRSStage.GURU_1: 168,  # 1 week
        SRSStage.GURU_2: 336,  # 2 weeks
        SRSStage.MASTER: 720,  # 1 month
        SRSStage.ENLIGHTENED: 2880,  # 4 months
        SRSStage.BURNED: None  # No more reviews
    }
    
    @classmethod
    def get_next_stage(cls, current_stage: SRSStage, correct: bool) -> SRSStage:
        """Get the next SRS stage based on answer correctness"""
        stages = list(SRSStage)
        current_index = stages.index(current_stage)
        
        if correct:
            # Move to next stage if not already at the highest
            if current_index < len(stages) - 1:
                return stages[current_index + 1]
            return current_stage
        else:
            # Go back to Apprentice I on incorrect answer
            return SRSStage.APPRENTICE_1
    
    @classmethod
    def calculate_next_review(cls, stage: SRSStage) -> Optional[datetime]:
        """Calculate when the next review should occur"""
        if stage == SRSStage.BURNED:
            return None
        
        interval_hours = cls.INTERVALS[stage]
        return datetime.now() + timedelta(hours=interval_hours)
    
    @classmethod
    def update_progress(cls, entry: GrammarEntry, correct: bool) -> GrammarEntry:
        """Update grammar entry progress after a review"""
        entry.last_reviewed = datetime.now()
        
        if correct:
            entry.correct_answers += 1
        else:
            entry.incorrect_answers += 1
        
        # Update lesson status if this is the first review
        if entry.lesson_status == LessonStatus.AVAILABLE:
            entry.lesson_status = LessonStatus.IN_PROGRESS
        
        entry.srs_stage = cls.get_next_stage(entry.srs_stage, correct)
        entry.next_review = cls.calculate_next_review(entry.srs_stage)
        
        return entry

class GrammarDatabase:
    """Database manager for grammar entries"""
    
    def __init__(self, db_path: str = "grammar.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS grammar_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grammar TEXT NOT NULL,
                    grammar_kana TEXT,
                    usage TEXT,
                    meaning TEXT,
                    example1_ja TEXT,
                    example1_en TEXT,
                    example2_ja TEXT,
                    example2_en TEXT,
                    note TEXT,
                    learned_date TEXT,
                    srs_stage TEXT DEFAULT 'Apprentice I',
                    next_review TEXT,
                    correct_answers INTEGER DEFAULT 0,
                    incorrect_answers INTEGER DEFAULT 0,
                    last_reviewed TEXT,
                    lesson_status TEXT DEFAULT 'Not Started'
                )
            """)
            
            # Add lesson_status column if it doesn't exist (for existing databases)
            try:
                conn.execute("ALTER TABLE grammar_entries ADD COLUMN lesson_status TEXT DEFAULT 'In Progress'")
                # Update existing entries to have proper lesson status
                conn.execute("UPDATE grammar_entries SET lesson_status = 'In Progress' WHERE lesson_status IS NULL")
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists, but make sure existing entries have proper status
                conn.execute("UPDATE grammar_entries SET lesson_status = 'In Progress' WHERE lesson_status IS NULL OR lesson_status = ''")
                conn.commit()
                
            # Create settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Set default settings
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_lesson_limit', '15')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_start_lessons', 'true')")
            
            conn.commit()
    
    def add_entry(self, entry: GrammarEntry) -> int:
        """Add a new grammar entry to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO grammar_entries 
                (grammar, grammar_kana, usage, meaning, example1_ja, example1_en, 
                 example2_ja, example2_en, note, learned_date, srs_stage, next_review,
                 correct_answers, incorrect_answers, last_reviewed, lesson_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.grammar, entry.grammar_kana, entry.usage, entry.meaning,
                entry.example1_ja, entry.example1_en, entry.example2_ja, entry.example2_en,
                entry.note, 
                entry.learned_date.isoformat() if entry.learned_date else None,
                entry.srs_stage.value,
                entry.next_review.isoformat() if entry.next_review else None,
                entry.correct_answers, entry.incorrect_answers,
                entry.last_reviewed.isoformat() if entry.last_reviewed else None,
                entry.lesson_status.value
            ))
            return cursor.lastrowid or 0
    
    def update_entry(self, entry: GrammarEntry):
        """Update an existing grammar entry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE grammar_entries SET
                    grammar=?, grammar_kana=?, usage=?, meaning=?, 
                    example1_ja=?, example1_en=?, example2_ja=?, example2_en=?,
                    note=?, learned_date=?, srs_stage=?, next_review=?,
                    correct_answers=?, incorrect_answers=?, last_reviewed=?, lesson_status=?
                WHERE id=?
            """, (
                entry.grammar, entry.grammar_kana, entry.usage, entry.meaning,
                entry.example1_ja, entry.example1_en, entry.example2_ja, entry.example2_en,
                entry.note,
                entry.learned_date.isoformat() if entry.learned_date else None,
                entry.srs_stage.value,
                entry.next_review.isoformat() if entry.next_review else None,
                entry.correct_answers, entry.incorrect_answers,
                entry.last_reviewed.isoformat() if entry.last_reviewed else None,
                entry.lesson_status.value,
                entry.id
            ))
    
    def get_entry(self, entry_id: int) -> Optional[GrammarEntry]:
        """Get a grammar entry by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM grammar_entries WHERE id=?", (entry_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_entry(row)
        return None
    
    def get_all_entries(self) -> List[GrammarEntry]:
        """Get all grammar entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM grammar_entries ORDER BY id")
            return [self._row_to_entry(row) for row in cursor.fetchall()]
    
    def get_due_reviews(self) -> List[GrammarEntry]:
        """Get entries that are due for review"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM grammar_entries 
                WHERE next_review <= ? AND srs_stage != 'Burned'
                ORDER BY next_review
            """, (now,))
            return [self._row_to_entry(row) for row in cursor.fetchall()]
    
    def get_entries_by_stage(self, stage: SRSStage) -> List[GrammarEntry]:
        """Get all entries at a specific SRS stage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM grammar_entries WHERE srs_stage = ?
            """, (stage.value,))
            return [self._row_to_entry(row) for row in cursor.fetchall()]
    
    def get_entries_by_lesson_status(self, status: LessonStatus) -> List[GrammarEntry]:
        """Get all entries with a specific lesson status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM grammar_entries WHERE lesson_status = ? ORDER BY id
            """, (status.value,))
            return [self._row_to_entry(row) for row in cursor.fetchall()]
    
    def start_lessons(self, limit: int) -> List[GrammarEntry]:
        """Start lessons for up to 'limit' new entries"""
        with sqlite3.connect(self.db_path) as conn:
            # Get not started entries
            cursor = conn.execute("""
                SELECT * FROM grammar_entries 
                WHERE lesson_status = ? 
                ORDER BY id LIMIT ?
            """, (LessonStatus.NOT_STARTED.value, limit))
            
            entries = [self._row_to_entry(row) for row in cursor.fetchall()]
            
            # Update their status to available and set for immediate review
            for entry in entries:
                entry.lesson_status = LessonStatus.AVAILABLE
                entry.next_review = datetime.now()
                self.update_entry(entry)
            
            return entries
    
    def get_lesson_summary(self) -> dict:
        """Get summary of lesson status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT lesson_status, COUNT(*) FROM grammar_entries 
                GROUP BY lesson_status
            """)
            
            summary = {status.value: 0 for status in LessonStatus}
            for status, count in cursor.fetchall():
                summary[status] = count
                
            return summary
    
    # Settings methods
    def get_setting(self, key: str, default: str = "") -> str:
        """Get a setting value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
    
    def _row_to_entry(self, row) -> GrammarEntry:
        """Convert database row to GrammarEntry object"""
        # Based on actual database schema:
        # id, grammar, grammar_kana, usage, meaning, example1_ja, example1_en, 
        # example2_ja, example2_en, note, learned_date, srs_stage, next_review,
        # correct_answers, incorrect_answers, last_reviewed, lesson_status
        
        if len(row) >= 17:  # New schema with lesson_status at the end
            lesson_status_value = row[16] if row[16] else "In Progress"
            next_review_index = 12
            correct_answers_index = 13
            incorrect_answers_index = 14
            last_reviewed_index = 15
        else:  # Old schema without lesson_status
            lesson_status_value = "In Progress"  # Default for existing entries
            next_review_index = 12
            correct_answers_index = 13
            incorrect_answers_index = 14
            last_reviewed_index = 15
        
        return GrammarEntry(
            id=row[0],
            grammar=row[1],
            grammar_kana=row[2] or "",
            usage=row[3] or "",
            meaning=row[4] or "",
            example1_ja=row[5] or "",
            example1_en=row[6] or "",
            example2_ja=row[7] or "",
            example2_en=row[8] or "",
            note=row[9] or "",
            learned_date=datetime.fromisoformat(row[10]) if row[10] else None,
            srs_stage=SRSStage(row[11]),
            lesson_status=LessonStatus(lesson_status_value),
            next_review=datetime.fromisoformat(row[next_review_index]) if row[next_review_index] else None,
            correct_answers=row[correct_answers_index],
            incorrect_answers=row[incorrect_answers_index],
            last_reviewed=datetime.fromisoformat(row[last_reviewed_index]) if row[last_reviewed_index] else None
        )

def parse_grammar_file(file_path: str, db: GrammarDatabase):
    """Parse the TSV grammar file and populate the database"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split by lines and skip header
    lines = content.strip().split('\n')[1:]
    
    for line in lines:
        if line.strip():
            # Try to parse the specific format we see in the file
            # The format appears to be: grammar \t [rest of the data]
            parts = line.split('\t')
            if len(parts) >= 2:
                grammar = parts[0]
                rest = parts[1]
                
                # Try to extract information from the rest using patterns
                # This is a simple heuristic parser for this specific format
                try:
                    # Split the rest by multiple spaces to get approximate fields
                    fields = [f.strip() for f in rest.split('  ') if f.strip()]
                    
                    # Basic extraction - this may need refinement
                    grammar_kana = grammar  # Same as grammar for now
                    usage = fields[0] if len(fields) > 0 else ""
                    meaning = fields[1] if len(fields) > 1 else ""
                    
                    # Look for Japanese and English example patterns
                    example1_ja = ""
                    example1_en = ""
                    example2_ja = ""
                    example2_en = ""
                    note = ""
                    
                    # Simple heuristic to find examples
                    for field in fields[2:]:
                        if any(char in field for char in 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'):
                            if not example1_ja:
                                example1_ja = field
                            elif not example2_ja:
                                example2_ja = field
                        elif field and not any(char in field for char in 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'):
                            if example1_ja and not example1_en:
                                example1_en = field
                            elif example2_ja and not example2_en:
                                example2_en = field
                    
                    entry = GrammarEntry(
                        grammar=grammar,
                        grammar_kana=grammar_kana,
                        usage=usage,
                        meaning=meaning,
                        example1_ja=example1_ja,
                        example1_en=example1_en,
                        example2_ja=example2_ja,
                        example2_en=example2_en,
                        note=note,
                        learned_date=datetime.now(),
                        lesson_status=LessonStatus.NOT_STARTED,
                        next_review=None  # Will be set when lesson starts
                    )
                    db.add_entry(entry)
                    
                except (IndexError, ValueError):
                    # Skip malformed entries
                    continue
