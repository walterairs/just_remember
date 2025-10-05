import sys
import random
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QLineEdit,
    QSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from fuzzywuzzy import fuzz

from models import (
    GrammarEntry,
    GrammarDatabase,
    SRSManager,
    SRSStage,
    parse_grammar_file,
    LessonStatus,
)


class ReviewWidget(QWidget):
    """Widget for reviewing grammar entries"""

    review_completed = pyqtSignal(bool)  # Signal emitted when review is completed

    def __init__(self):
        super().__init__()
        self.current_entry: Optional[GrammarEntry] = None
        self.show_answer = False
        self.user_answered = False
        self.acceptable_answers = []
        self.last_answer_correct = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Progress section
        progress_group = QGroupBox("Review Progress")
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("No reviews due")
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)

        # Question section
        question_group = QGroupBox("Grammar Review")
        question_layout = QVBoxLayout()

        self.grammar_label = QLabel("")
        self.grammar_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.grammar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.usage_label = QLabel("")
        self.usage_label.setFont(QFont("Arial", 12))
        self.usage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.usage_label.setWordWrap(True)

        self.meaning_label = QLabel("")
        self.meaning_label.setFont(QFont("Arial", 12))
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meaning_label.setWordWrap(True)
        self.meaning_label.hide()

        self.examples_text = QTextEdit()
        self.examples_text.setMaximumHeight(150)
        self.examples_text.setReadOnly(True)
        self.examples_text.hide()

        self.note_label = QLabel("")
        self.note_label.setFont(QFont("Arial", 10))
        self.note_label.setStyleSheet("color: gray;")
        self.note_label.setWordWrap(True)
        self.note_label.hide()

        # Answer input section
        answer_group = QGroupBox("Your Answer")
        answer_layout = QVBoxLayout()
        
        self.answer_prompt = QLabel("What does this grammar pattern mean?")
        self.answer_prompt.setFont(QFont("Arial", 11))
        
        self.answer_input = QLineEdit()
        self.answer_input.setFont(QFont("Arial", 12))
        self.answer_input.setPlaceholderText("Type the meaning in English...")
        self.answer_input.returnPressed.connect(self.check_answer)
        
        self.feedback_label = QLabel("")
        self.feedback_label.setFont(QFont("Arial", 10))
        self.feedback_label.setWordWrap(True)
        self.feedback_label.hide()
        
        answer_layout.addWidget(self.answer_prompt)
        answer_layout.addWidget(self.answer_input)
        answer_layout.addWidget(self.feedback_label)
        answer_group.setLayout(answer_layout)

        question_layout.addWidget(self.grammar_label)
        question_layout.addWidget(self.usage_label)
        question_layout.addWidget(answer_group)
        question_layout.addWidget(self.meaning_label)
        question_layout.addWidget(self.examples_text)
        question_layout.addWidget(self.note_label)
        question_group.setLayout(question_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.check_answer_btn = QPushButton("Check Answer")
        self.check_answer_btn.clicked.connect(self.check_answer)

        self.show_answer_btn = QPushButton("Show Full Answer")
        self.show_answer_btn.clicked.connect(self.show_answer_clicked)
        self.show_answer_btn.hide()

        self.next_btn = QPushButton("Next ➤")
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.hide()

        button_layout.addWidget(self.check_answer_btn)
        button_layout.addWidget(self.show_answer_btn)
        button_layout.addWidget(self.next_btn)

        layout.addWidget(progress_group)
        layout.addWidget(question_group)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def set_entry(self, entry: GrammarEntry, total_reviews: int, current_index: int):
        """Set the current grammar entry to review"""
        self.current_entry = entry
        self.show_answer = False
        self.user_answered = False
        
        # Prepare acceptable answers for fuzzy matching
        self.acceptable_answers = self._prepare_acceptable_answers(entry)

        # Update progress
        self.progress_label.setText(f"Review {current_index + 1} of {total_reviews}")
        self.progress_bar.setMaximum(total_reviews)
        self.progress_bar.setValue(current_index + 1)

        # Update display
        self.grammar_label.setText(entry.grammar)
        self.usage_label.setText(f"Usage: {entry.usage}")
        
        # Reset answer input
        self.answer_input.clear()
        self.answer_input.setEnabled(True)
        self.answer_input.setFocus()
        self.feedback_label.hide()

        # Hide answer elements and reset buttons
        self.meaning_label.hide()
        self.examples_text.hide()
        self.note_label.hide()
        self.show_answer_btn.hide()
        self.next_btn.hide()
        self.check_answer_btn.show()

    def show_answer_clicked(self):
        """Show the answer and rating buttons"""
        if not self.current_entry:
            return

        self.show_answer = True

        # Show answer
        self.meaning_label.setText(f"Meaning: {self.current_entry.meaning}")
        self.meaning_label.show()

        # Show examples
        examples_text = ""
        if self.current_entry.example1_ja:
            examples_text += f"Example 1:\n{self.current_entry.example1_ja}\n{self.current_entry.example1_en}\n\n"
        if self.current_entry.example2_ja:
            examples_text += f"Example 2:\n{self.current_entry.example2_ja}\n{self.current_entry.example2_en}"

        self.examples_text.setPlainText(examples_text)
        self.examples_text.show()

        # Show note if exists
        if self.current_entry.note:
            self.note_label.setText(f"Note: {self.current_entry.note}")
            self.note_label.show()
            
    def _prepare_acceptable_answers(self, entry: GrammarEntry) -> List[str]:
        """Prepare list of acceptable answers for fuzzy matching"""
        answers = []
        
        # Add the main meaning
        if entry.meaning:
            answers.append(entry.meaning.lower().strip())
            
        # Add variations and common simplifications
        meaning = entry.meaning.lower()
        
        # Remove common prefixes/suffixes
        simplified = meaning.replace("～ is", "").replace("～ am", "").replace("～ are", "")
        simplified = simplified.replace("～", "").strip()
        if simplified and simplified not in answers:
            answers.append(simplified)
            
        # Split on common separators and add individual meanings
        for separator in [",", ";", ".", "!", "?"]:
            if separator in meaning:
                parts = [part.strip() for part in meaning.split(separator) if part.strip()]
                for part in parts:
                    clean_part = part.replace("～", "").strip()
                    if clean_part and len(clean_part) > 2 and clean_part not in answers:
                        answers.append(clean_part)
        
        return answers
    
    def check_answer(self):
        """Check the user's typed answer against acceptable answers"""
        if not self.current_entry or self.user_answered:
            return
            
        user_answer = self.answer_input.text().strip().lower()
        if not user_answer:
            return
            
        self.user_answered = True
        self.answer_input.setEnabled(False)
        
        # Check against acceptable answers with fuzzy matching
        best_match_score = 0
        best_match = ""
        is_correct = False
        
        for acceptable in self.acceptable_answers:
            # Use different fuzzy matching algorithms
            ratio_score = fuzz.ratio(user_answer, acceptable)
            partial_score = fuzz.partial_ratio(user_answer, acceptable)
            token_score = fuzz.token_sort_ratio(user_answer, acceptable)
            
            # Take the best score from different algorithms
            best_score = max(ratio_score, partial_score, token_score)
            
            if best_score > best_match_score:
                best_match_score = best_score
                best_match = acceptable
        
        # Determine if answer is correct (threshold: 75%)
        threshold = 75
        is_correct = best_match_score >= threshold
        
        # Show feedback
        if is_correct:
            self.feedback_label.setText(
                f"✓ Correct! (Match: {best_match_score}%)\nYour answer: '{user_answer}'\nAccepted: '{best_match}'"
            )
            self.feedback_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.feedback_label.setText(
                f"✗ Not quite right (Match: {best_match_score}%)\nYour answer: '{user_answer}'\nExpected: '{self.current_entry.meaning}'"
            )
            self.feedback_label.setStyleSheet("color: #f44336; font-weight: bold;")
            
        self.feedback_label.show()
        
        # Store the result for later submission
        self.last_answer_correct = is_correct
        
        # Show additional options
        self.check_answer_btn.hide()
        self.show_answer_btn.show()
        self.next_btn.show()
        
        # Auto-show full answer if incorrect
        if not is_correct:
            self.show_answer_clicked()
    
    def next_question(self):
        """Move to the next question"""
        if hasattr(self, 'last_answer_correct') and self.current_entry:
            self.review_completed.emit(self.last_answer_correct)


class SettingsWidget(QWidget):
    """Widget for application settings"""
    
    def __init__(self, db: GrammarDatabase):
        super().__init__()
        self.db = db
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Lesson settings
        lesson_group = QGroupBox("Lesson Settings")
        lesson_layout = QGridLayout()
        
        # Daily lesson limit
        lesson_layout.addWidget(QLabel("Daily Lesson Limit:"), 0, 0)
        self.lesson_limit_spinbox = QSpinBox()
        self.lesson_limit_spinbox.setMinimum(1)
        self.lesson_limit_spinbox.setMaximum(50)
        self.lesson_limit_spinbox.setValue(15)
        self.lesson_limit_spinbox.valueChanged.connect(self.save_settings)
        lesson_layout.addWidget(self.lesson_limit_spinbox, 0, 1)
        
        # Auto start lessons
        self.auto_start_checkbox = QCheckBox("Auto-start lessons when importing")
        self.auto_start_checkbox.setChecked(True)
        self.auto_start_checkbox.stateChanged.connect(self.save_settings)
        lesson_layout.addWidget(self.auto_start_checkbox, 1, 0, 1, 2)
        
        lesson_group.setLayout(lesson_layout)
        
        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        
        self.start_lessons_btn = QPushButton("Start New Lessons")
        self.start_lessons_btn.clicked.connect(self.start_lessons)
        
        self.reset_all_btn = QPushButton("Reset All Progress")
        self.reset_all_btn.clicked.connect(self.reset_all_progress)
        self.reset_all_btn.setStyleSheet("background-color: #f44336; color: white;")
        
        action_layout.addWidget(self.start_lessons_btn)
        action_layout.addWidget(self.reset_all_btn)
        action_group.setLayout(action_layout)
        
        # Lesson status display
        status_group = QGroupBox("Lesson Status")
        status_layout = QGridLayout()
        
        self.not_started_label = QLabel("0")
        self.available_label = QLabel("0")
        self.in_progress_label = QLabel("0")
        
        status_layout.addWidget(QLabel("Not Started:"), 0, 0)
        status_layout.addWidget(self.not_started_label, 0, 1)
        status_layout.addWidget(QLabel("Available for Lessons:"), 1, 0)
        status_layout.addWidget(self.available_label, 1, 1)
        status_layout.addWidget(QLabel("In Progress (SRS):"), 2, 0)
        status_layout.addWidget(self.in_progress_label, 2, 1)
        
        status_group.setLayout(status_layout)
        
        layout.addWidget(lesson_group)
        layout.addWidget(status_group)
        layout.addWidget(action_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load settings from database"""
        limit = int(self.db.get_setting("daily_lesson_limit", "15"))
        auto_start = self.db.get_setting("auto_start_lessons", "true") == "true"
        
        self.lesson_limit_spinbox.setValue(limit)
        self.auto_start_checkbox.setChecked(auto_start)
        
        self.update_status()
    
    def save_settings(self):
        """Save settings to database"""
        self.db.set_setting("daily_lesson_limit", str(self.lesson_limit_spinbox.value()))
        self.db.set_setting("auto_start_lessons", "true" if self.auto_start_checkbox.isChecked() else "false")
    
    def start_lessons(self):
        """Start new lessons"""
        limit = self.lesson_limit_spinbox.value()
        not_started = self.db.get_entries_by_lesson_status(LessonStatus.NOT_STARTED)
        
        if not not_started:
            QMessageBox.information(self, "No New Items", "No new grammar entries available for lessons!")
            return
        
        available_count = len(self.db.get_entries_by_lesson_status(LessonStatus.AVAILABLE))
        if available_count > 0:
            reply = QMessageBox.question(
                self, "Lessons Already Available", 
                f"You have {available_count} lessons already available. Start {limit} more?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        started_entries = self.db.start_lessons(limit)
        QMessageBox.information(
            self, "Lessons Started", 
            f"Started {len(started_entries)} new lessons! They are now available for review."
        )
        self.update_status()
    
    def reset_all_progress(self):
        """Reset all entries to not started"""
        reply = QMessageBox.question(
            self, "Reset All Progress", 
            "This will reset ALL grammar entries to 'Not Started' status. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            all_entries = self.db.get_all_entries()
            for entry in all_entries:
                entry.lesson_status = LessonStatus.NOT_STARTED
                entry.srs_stage = SRSStage.APPRENTICE_1
                entry.next_review = None
                entry.correct_answers = 0
                entry.incorrect_answers = 0
                entry.last_reviewed = None
                self.db.update_entry(entry)
            
            QMessageBox.information(self, "Progress Reset", "All progress has been reset!")
            self.update_status()
    
    def update_status(self):
        """Update lesson status display"""
        summary = self.db.get_lesson_summary()
        self.not_started_label.setText(str(summary.get("Not Started", 0)))
        self.available_label.setText(str(summary.get("Available", 0)))
        self.in_progress_label.setText(str(summary.get("In Progress", 0)))


class StatisticsWidget(QWidget):
    """Widget for displaying learning statistics"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # SRS Stage distribution
        srs_group = QGroupBox("SRS Stage Distribution")
        srs_layout = QGridLayout()

        self.stage_labels = {}
        stages = list(SRSStage)
        for i, stage in enumerate(stages):
            label = QLabel(stage.value + ":")
            count_label = QLabel("0")
            count_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            # Color coding for stages
            if "Apprentice" in stage.value:
                count_label.setStyleSheet("color: #FF69B4; font-weight: bold;")
            elif "Guru" in stage.value:
                count_label.setStyleSheet("color: #9C27B0; font-weight: bold;")
            elif stage.value == "Master":
                count_label.setStyleSheet("color: #2196F3; font-weight: bold;")
            elif stage.value == "Enlightened":
                count_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            elif stage.value == "Burned":
                count_label.setStyleSheet("color: #FFC107; font-weight: bold;")

            srs_layout.addWidget(label, i, 0)
            srs_layout.addWidget(count_label, i, 1)
            self.stage_labels[stage] = count_label

        srs_group.setLayout(srs_layout)

        # Overall statistics
        stats_group = QGroupBox("Overall Statistics")
        stats_layout = QGridLayout()

        self.total_entries_label = QLabel("0")
        self.total_reviews_label = QLabel("0")
        self.accuracy_label = QLabel("0%")
        self.due_reviews_label = QLabel("0")

        stats_layout.addWidget(QLabel("Total Entries:"), 0, 0)
        stats_layout.addWidget(self.total_entries_label, 0, 1)
        stats_layout.addWidget(QLabel("Total Reviews:"), 1, 0)
        stats_layout.addWidget(self.total_reviews_label, 1, 1)
        stats_layout.addWidget(QLabel("Accuracy:"), 2, 0)
        stats_layout.addWidget(self.accuracy_label, 2, 1)
        stats_layout.addWidget(QLabel("Due Reviews:"), 3, 0)
        stats_layout.addWidget(self.due_reviews_label, 3, 1)

        stats_group.setLayout(stats_layout)

        layout.addWidget(srs_group)
        layout.addWidget(stats_group)
        layout.addStretch()

        self.setLayout(layout)

    def update_statistics(self, db: GrammarDatabase):
        """Update statistics display"""
        all_entries = db.get_all_entries()
        due_entries = db.get_due_reviews()

        # Update stage distribution
        for stage in SRSStage:
            count = len(db.get_entries_by_stage(stage))
            self.stage_labels[stage].setText(str(count))

        # Update overall stats
        self.total_entries_label.setText(str(len(all_entries)))
        self.due_reviews_label.setText(str(len(due_entries)))

        # Calculate total reviews and accuracy
        total_reviews = sum(
            entry.correct_answers + entry.incorrect_answers for entry in all_entries
        )
        total_correct = sum(entry.correct_answers for entry in all_entries)

        self.total_reviews_label.setText(str(total_reviews))
        if total_reviews > 0:
            accuracy = (total_correct / total_reviews) * 100
            self.accuracy_label.setText(f"{accuracy:.1f}%")
        else:
            self.accuracy_label.setText("0%")
    """Widget for displaying learning statistics"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # SRS Stage distribution
        srs_group = QGroupBox("SRS Stage Distribution")
        srs_layout = QGridLayout()

        self.stage_labels = {}
        stages = list(SRSStage)
        for i, stage in enumerate(stages):
            label = QLabel(stage.value + ":")
            count_label = QLabel("0")
            count_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            # Color coding for stages
            if "Apprentice" in stage.value:
                count_label.setStyleSheet("color: #FF69B4; font-weight: bold;")
            elif "Guru" in stage.value:
                count_label.setStyleSheet("color: #9C27B0; font-weight: bold;")
            elif stage.value == "Master":
                count_label.setStyleSheet("color: #2196F3; font-weight: bold;")
            elif stage.value == "Enlightened":
                count_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            elif stage.value == "Burned":
                count_label.setStyleSheet("color: #FFC107; font-weight: bold;")

            srs_layout.addWidget(label, i, 0)
            srs_layout.addWidget(count_label, i, 1)
            self.stage_labels[stage] = count_label

        srs_group.setLayout(srs_layout)

        # Overall statistics
        stats_group = QGroupBox("Overall Statistics")
        stats_layout = QGridLayout()

        self.total_entries_label = QLabel("0")
        self.total_reviews_label = QLabel("0")
        self.accuracy_label = QLabel("0%")
        self.due_reviews_label = QLabel("0")

        stats_layout.addWidget(QLabel("Total Entries:"), 0, 0)
        stats_layout.addWidget(self.total_entries_label, 0, 1)
        stats_layout.addWidget(QLabel("Total Reviews:"), 1, 0)
        stats_layout.addWidget(self.total_reviews_label, 1, 1)
        stats_layout.addWidget(QLabel("Accuracy:"), 2, 0)
        stats_layout.addWidget(self.accuracy_label, 2, 1)
        stats_layout.addWidget(QLabel("Due Reviews:"), 3, 0)
        stats_layout.addWidget(self.due_reviews_label, 3, 1)

        stats_group.setLayout(stats_layout)

        layout.addWidget(srs_group)
        layout.addWidget(stats_group)
        layout.addStretch()

        self.setLayout(layout)

    def update_statistics(self, db: GrammarDatabase):
        """Update statistics display"""
        all_entries = db.get_all_entries()
        due_entries = db.get_due_reviews()

        # Update stage distribution
        for stage in SRSStage:
            count = len(db.get_entries_by_stage(stage))
            self.stage_labels[stage].setText(str(count))

        # Update overall stats
        self.total_entries_label.setText(str(len(all_entries)))
        self.due_reviews_label.setText(str(len(due_entries)))

        # Calculate total reviews and accuracy
        total_reviews = sum(
            entry.correct_answers + entry.incorrect_answers for entry in all_entries
        )
        total_correct = sum(entry.correct_answers for entry in all_entries)

        self.total_reviews_label.setText(str(total_reviews))
        if total_reviews > 0:
            accuracy = (total_correct / total_reviews) * 100
            self.accuracy_label.setText(f"{accuracy:.1f}%")
        else:
            self.accuracy_label.setText("0%")


class GrammarListWidget(QWidget):
    """Widget for displaying all grammar entries in a table"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Grammar", "Meaning", "Lesson Status", "SRS Stage", "Next Review"]
        )

        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_table(self, entries: List[GrammarEntry]):
        """Update the table with grammar entries"""
        self.table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.grammar))
            self.table.setItem(row, 1, QTableWidgetItem(entry.meaning))
            self.table.setItem(row, 2, QTableWidgetItem(entry.lesson_status.value))
            self.table.setItem(row, 3, QTableWidgetItem(entry.srs_stage.value))

            next_review = (
                "Burned"
                if entry.srs_stage == SRSStage.BURNED
                else "Not Started"
                if entry.lesson_status == LessonStatus.NOT_STARTED
                else entry.next_review.strftime("%Y-%m-%d %H:%M")
                if entry.next_review
                else "Not set"
            )
            self.table.setItem(row, 4, QTableWidgetItem(next_review))

        self.table.resizeColumnsToContents()


class JustRememberApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.db = GrammarDatabase()
        self.current_reviews: List[GrammarEntry] = []
        self.current_review_index = 0
        self.init_ui()
        self.update_displays()

    def init_ui(self):
        self.setWindowTitle("Just Remember - Japanese Grammar SRS")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Review tab
        self.review_widget = ReviewWidget()
        self.review_widget.review_completed.connect(self.handle_review_completed)
        self.tab_widget.addTab(self.review_widget, "Review")

        # Statistics tab
        self.stats_widget = StatisticsWidget()
        self.tab_widget.addTab(self.stats_widget, "Statistics")
        
        # Settings tab
        self.settings_widget = SettingsWidget(self.db)
        self.tab_widget.addTab(self.settings_widget, "Settings")

        # Grammar list tab
        self.grammar_list_widget = GrammarListWidget()
        self.tab_widget.addTab(self.grammar_list_widget, "All Grammar")

        # Control panel
        control_group = QGroupBox("Controls")
        control_layout = QHBoxLayout()

        self.start_review_btn = QPushButton("Start Review Session")
        self.start_review_btn.clicked.connect(self.start_review_session)

        self.import_btn = QPushButton("Import Grammar File")
        self.import_btn.clicked.connect(self.import_grammar_file)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_displays)

        self.make_due_btn = QPushButton("Make All Due")
        self.make_due_btn.clicked.connect(self.make_all_due)
        self.make_due_btn.setToolTip("Make all entries immediately available for review")

        control_layout.addWidget(self.start_review_btn)
        control_layout.addWidget(self.import_btn)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.make_due_btn)
        control_group.setLayout(control_layout)

        layout.addWidget(control_group)
        layout.addWidget(self.tab_widget)

        central_widget.setLayout(layout)

        # Set up refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_displays)
        self.refresh_timer.start(60000)  # Refresh every minute

    def start_review_session(self):
        """Start a new review session"""
        # Get due reviews (only available or in-progress items)
        all_due = self.db.get_due_reviews()
        self.current_reviews = [
            entry for entry in all_due 
            if entry.lesson_status in [LessonStatus.AVAILABLE, LessonStatus.IN_PROGRESS]
        ]

        if not self.current_reviews:
            # Check if there are lessons that could be started
            not_started = self.db.get_entries_by_lesson_status(LessonStatus.NOT_STARTED)
            if not_started:
                reply = QMessageBox.question(
                    self, "No Reviews Due", 
                    f"No reviews are due, but you have {len(not_started)} new items available. Start lessons?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    # Auto-start some lessons
                    limit = int(self.db.get_setting("daily_lesson_limit", "15"))
                    started = self.db.start_lessons(min(limit, len(not_started)))
                    self.current_reviews = started
                    self.update_displays()
                else:
                    return
            else:
                QMessageBox.information(
                    self, "No Reviews", "No grammar entries are due for review!"
                )
                return

        # Shuffle reviews for variety
        random.shuffle(self.current_reviews)
        self.current_review_index = 0

        # Switch to review tab and start first review
        self.tab_widget.setCurrentIndex(0)
        self.show_current_review()

    def show_current_review(self):
        """Show the current review entry"""
        if self.current_review_index < len(self.current_reviews):
            entry = self.current_reviews[self.current_review_index]
            self.review_widget.set_entry(
                entry, len(self.current_reviews), self.current_review_index
            )
        else:
            # All reviews completed
            QMessageBox.information(
                self,
                "Session Complete",
                f"Review session completed! You reviewed {len(self.current_reviews)} items.",
            )
            self.current_reviews = []
            self.current_review_index = 0
            self.update_displays()

    def handle_review_completed(self, correct: bool):
        """Handle completion of a review"""
        if self.current_review_index < len(self.current_reviews):
            entry = self.current_reviews[self.current_review_index]

            # Update entry progress
            updated_entry = SRSManager.update_progress(entry, correct)
            self.db.update_entry(updated_entry)

            # Move to next review
            self.current_review_index += 1
            self.show_current_review()

    def import_grammar_file(self):
        """Import grammar entries from a TSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Grammar File", "", "TSV Files (*.txt *.tsv);;All Files (*)"
        )

        if file_path:
            try:
                parse_grammar_file(file_path, self.db)
                
                # Check if auto-start lessons is enabled
                auto_start = self.db.get_setting("auto_start_lessons", "true") == "true"
                if auto_start:
                    limit = int(self.db.get_setting("daily_lesson_limit", "15"))
                    not_started = self.db.get_entries_by_lesson_status(LessonStatus.NOT_STARTED)
                    if not_started:
                        started = self.db.start_lessons(min(limit, len(not_started)))
                        QMessageBox.information(
                            self, "Import Successful", 
                            f"Grammar entries imported successfully!\n{len(started)} lessons auto-started."
                        )
                    else:
                        QMessageBox.information(
                            self, "Import Successful", "Grammar entries imported successfully!"
                        )
                else:
                    QMessageBox.information(
                        self, "Import Successful", "Grammar entries imported successfully!"
                    )
                
                self.update_displays()
            except (OSError, ValueError, IndexError) as e:
                QMessageBox.critical(
                    self, "Import Error", f"Failed to import file:\n{str(e)}"
                )

    def make_all_due(self):
        """Make all entries immediately due for review"""
        from datetime import datetime
        
        all_entries = self.db.get_all_entries()
        if not all_entries:
            QMessageBox.information(self, "No Entries", "No grammar entries found to make due!")
            return
        
        # Update all available and in-progress entries to be due now
        count = 0
        for entry in all_entries:
            if entry.lesson_status in [LessonStatus.AVAILABLE, LessonStatus.IN_PROGRESS] and entry.srs_stage != SRSStage.BURNED:
                entry.next_review = datetime.now()
                self.db.update_entry(entry)
                count += 1
        
        QMessageBox.information(
            self, "Success", f"Made {count} grammar entries immediately due for review!"
        )
        self.update_displays()

    def update_displays(self):
        """Update all display widgets"""
        self.stats_widget.update_statistics(self.db)
        self.settings_widget.update_status()

        all_entries = self.db.get_all_entries()
        self.grammar_list_widget.update_table(all_entries)

        # Count only available and in-progress due reviews
        all_due = self.db.get_due_reviews()
        due_count = len([
            entry for entry in all_due 
            if entry.lesson_status in [LessonStatus.AVAILABLE, LessonStatus.IN_PROGRESS]
        ])
        
        # Check for not started items
        not_started_count = len(self.db.get_entries_by_lesson_status(LessonStatus.NOT_STARTED))
        
        if due_count > 0:
            self.start_review_btn.setText(f"Start Review Session ({due_count} due)")
        elif not_started_count > 0:
            self.start_review_btn.setText(f"Start Lessons ({not_started_count} new)")
        else:
            self.start_review_btn.setText("No Reviews Due")


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = JustRememberApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
