import os
import sys
import random
from collections import Counter
from typing import List, Set, Tuple


def resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource, works for both dev and PyInstaller."""
    if getattr(sys, '_MEIPASS', None):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


class WordleSolver:
    def __init__(self, answers_file: str = "answers-wordlist.txt",
                 valid_words_file: str = "valid-words.txt"):
        """Initialize the Wordle solver with word lists."""
        self.answers = self.load_words(resource_path(answers_file))
        self.valid_words = self.load_words(resource_path(valid_words_file))
        self.possible_answers = self.answers.copy()
        self.guessed_words = []
        self.guess_feedbacks = []
        self.constraints = {
            'correct_positions': {},  # position -> letter
            'wrong_positions': {},    # letter -> set of positions where it can't be
            'contains': set(),        # letters that must be in the word
            'excludes': set()         # letters that are not in the word
        }
        # Store history for undo functionality
        self.history = []  # List of (possible_answers, guessed_words, constraints) states
    
    def load_words(self, filename: str) -> List[str]:
        """Load words from a text file."""
        try:
            with open(filename, 'r') as file:
                return [word.strip().upper() for word in file if len(word.strip()) == 5]
        except FileNotFoundError:
            print(f"Warning: {filename} not found. Using fallback word list.")
            return self.get_fallback_words()
    
    def get_fallback_words(self) -> List[str]:
        """Fallback word list if files are not found."""
        return [
            "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT",
            "AFTER", "AGAIN", "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT",
            "ALIEN", "ALIGN", "ALIVE", "ALLOW", "ALONE", "ALONG", "ALTER", "ANGEL",
            "ANGER", "ANGLE", "ANGRY", "APART", "APPLE", "APPLY", "ARENA", "ARGUE",
            "ARISE", "ARRAY", "ASIDE", "ASSET", "AVOID", "AWAKE", "AWARD", "AWARE",
            "BADLY", "BAKER", "BASES", "BASIC", "BEACH", "BEGAN", "BEGIN", "BEING",
            "BELOW", "BENCH", "BILLY", "BIRTH", "BLACK", "BLAME", "BLANK", "BLIND",
            "BLOCK", "BLOOD", "BOARD", "BOAST", "BOATS", "BOBBY", "BONDS", "BOOKS",
            "BOOST", "BOOTH", "BOUND", "BRAIN", "BRAND", "BRASS", "BRAVE", "BREAD",
            "BREAK", "BREED", "BRIEF", "BRING", "BROAD", "BROKE", "BROWN", "BUILD"
        ]
    
    def add_feedback(self, guess: str, result: str):
        """
        Add feedback from a guess.
        result: 5-character string where:
        'G' = Green (correct letter, correct position)
        'Y' = Yellow (correct letter, wrong position)  
        'B' = Black/Gray (letter not in word)
        """
        guess = guess.upper()
        result = result.upper()
        
        if len(guess) != 5 or len(result) != 5:
            raise ValueError("Guess and result must be 5 characters long")
        
        # Save current state to history before making changes
        import copy
        self.history.append({
            'possible_answers': self.possible_answers.copy(),
            'guessed_words': self.guessed_words.copy(),
            'guess_feedbacks': self.guess_feedbacks.copy(),
            'constraints': copy.deepcopy(self.constraints)
        })

        self.guessed_words.append(guess)
        self.guess_feedbacks.append(result)
        
        # Count letters in the guess to handle duplicates properly
        guess_letter_count = Counter(guess)
        confirmed_letters = set()  # Letters we know are in the word
        
        # First pass: process greens and count confirmed letters
        for i, (letter, color) in enumerate(zip(guess, result)):
            if color == 'G':
                self.constraints['correct_positions'][i] = letter
                confirmed_letters.add(letter)
        
        # Second pass: process yellows
        for i, (letter, color) in enumerate(zip(guess, result)):
            if color == 'Y':
                confirmed_letters.add(letter)
                if letter not in self.constraints['wrong_positions']:
                    self.constraints['wrong_positions'][letter] = set()
                self.constraints['wrong_positions'][letter].add(i)
        
        # Third pass: process blacks, but be careful about duplicate letters
        for i, (letter, color) in enumerate(zip(guess, result)):
            if color == 'B':
                # Only exclude the letter if we haven't confirmed it's in the word
                if letter not in confirmed_letters:
                    self.constraints['excludes'].add(letter)
        
        # Update the contains set
        self.constraints['contains'].update(confirmed_letters)
        
        self.filter_possible_answers()
    
    def undo_last_feedback(self) -> bool:
        """
        Undo the most recent feedback addition.
        Returns True if successful, False if no history to undo.
        """
        if not self.history:
            return False
        
        # Restore the previous state
        previous_state = self.history.pop()
        self.possible_answers = previous_state['possible_answers']
        self.guessed_words = previous_state['guessed_words']
        self.guess_feedbacks = previous_state['guess_feedbacks']
        self.constraints = previous_state['constraints']
        
        return True
    
    def filter_possible_answers(self):
        """Filter possible answers based on current constraints."""
        filtered = []
        
        for word in self.possible_answers:
            if self.is_valid_word(word):
                filtered.append(word)
        
        self.possible_answers = filtered
    
    def get_all_valid_words_matching_constraints(self) -> List[str]:
        """Get all words from valid_words that match current constraints."""
        valid_matches = []
        for word in self.valid_words:
            if self.is_valid_word(word):
                valid_matches.append(word)
        return valid_matches
    
    def is_valid_word(self, word: str) -> bool:
        """Check if a word satisfies all current constraints."""
        word = word.upper()
        
        # Check correct positions
        for pos, letter in self.constraints['correct_positions'].items():
            if word[pos] != letter:
                return False
        
        # Check that required letters are present
        for letter in self.constraints['contains']:
            if letter not in word:
                return False
        
        # Check excluded letters
        for letter in self.constraints['excludes']:
            if letter in word:
                return False
        
        # Check wrong positions
        for letter, wrong_positions in self.constraints['wrong_positions'].items():
            for pos in wrong_positions:
                if word[pos] == letter:
                    return False
        
        return True
    
    def calculate_letter_frequencies(self, word_list: List[str] = None) -> dict:
        """Calculate letter frequencies in a given word list."""
        if word_list is None:
            word_list = self.possible_answers
        
        freq = Counter()
        for word in word_list:
            for letter in set(word):  # Use set to count each letter only once per word
                freq[letter] += 1
        return freq
    
    def score_word(self, word: str, word_list: List[str] = None) -> float:
        """Score a word based on letter frequency and uniqueness."""
        word = word.upper()
        letter_freq = self.calculate_letter_frequencies(word_list)
        
        # Base score from letter frequencies
        score = 0
        unique_letters = set(word)
        
        for letter in unique_letters:
            score += letter_freq.get(letter, 0)
        
        # Bonus for words with 5 unique letters
        if len(unique_letters) == 5:
            score *= 1.2
        
        # Penalty for repeated letters
        if len(unique_letters) < 5:
            score *= 0.8
        
        return score
    
    def get_best_guesses(self, count: int = 10) -> List[Tuple[str, float]]:
        """Get the best guess words ranked by score."""
        # Get all words that match constraints (from the full valid words list)
        all_valid_matches = self.get_all_valid_words_matching_constraints()
        
        if not all_valid_matches:
            return []
        
        # Score all valid guess words that satisfy constraints
        word_scores = []
        for word in all_valid_matches:
            if word not in self.guessed_words:
                score = self.score_word(word, all_valid_matches)
                word_scores.append((word, score))
        
        # Sort by score (descending)
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        return word_scores[:count]
    
    def find_guaranteed_solve_word(self) -> str:
        """Find a word that guarantees solving in 2 moves when few answers remain."""
        all_valid_matches = self.get_all_valid_words_matching_constraints()
        
        if len(all_valid_matches) > 8:
            return None
            
        # For each valid guess word, simulate all possible outcomes
        best_word = None
        min_max_remaining = float('inf')
        
        # Only check words that are actually in our word lists
        candidate_words = [word for word in self.valid_words if word not in self.guessed_words]
        
        for guess_word in candidate_words:
            max_remaining_after_guess = 0
            
            # Simulate each possible answer
            for answer in all_valid_matches:
                # Generate the feedback pattern for this guess/answer pair
                feedback = self.generate_feedback(guess_word, answer)
                
                # Count how many answers would remain after this feedback
                remaining_count = 0
                for candidate in all_valid_matches:
                    if self.would_match_feedback(guess_word, candidate, feedback):
                        remaining_count += 1
                
                max_remaining_after_guess = max(max_remaining_after_guess, remaining_count)
            
            # This word is better if it has a lower maximum remaining count
            if max_remaining_after_guess < min_max_remaining:
                min_max_remaining = max_remaining_after_guess
                best_word = guess_word
        
        # Only return if it's actually a good guaranteed solve (leaves ≤2 possibilities)
        return best_word if best_word and min_max_remaining <= 2 else None
    
    def generate_feedback(self, guess: str, answer: str) -> str:
        """Generate feedback pattern (GYBBB format) for a guess against an answer."""
        guess = guess.upper()
        answer = answer.upper()
        feedback = ['B'] * 5
        answer_letters = list(answer)
        
        # First pass: mark greens
        for i in range(5):
            if guess[i] == answer[i]:
                feedback[i] = 'G'
                answer_letters[i] = None  # Remove from consideration for yellows
        
        # Second pass: mark yellows
        for i in range(5):
            if feedback[i] == 'B' and guess[i] in answer_letters:
                # Find and remove the first occurrence
                for j in range(5):
                    if answer_letters[j] == guess[i]:
                        feedback[i] = 'Y'
                        answer_letters[j] = None
                        break
        
        return ''.join(feedback)
    
    def would_match_feedback(self, guess: str, candidate: str, expected_feedback: str) -> bool:
        """Check if a candidate word would produce the expected feedback for a given guess."""
        actual_feedback = self.generate_feedback(guess, candidate)
        return actual_feedback == expected_feedback
    
    def get_best_solve_suggestions(self, count: int = 10) -> List[Tuple[str, float]]:
        """Get the best words from possible answers ranked by score."""
        # First try to get suggestions from the original possible_answers
        if self.possible_answers:
            word_scores = []
            for word in self.possible_answers:
                if word not in self.guessed_words:
                    score = self.score_word(word)
                    word_scores.append((word, score))
            
            # Sort by score (descending)
            word_scores.sort(key=lambda x: x[1], reverse=True)
            
            return word_scores[:count]
        
        # Fallback: if no possible_answers remain, get from all valid words matching constraints
        all_valid_matches = self.get_all_valid_words_matching_constraints()
        
        if not all_valid_matches:
            return []
        
        word_scores = []
        for word in all_valid_matches:
            if word not in self.guessed_words:
                score = self.score_word(word, all_valid_matches)
                word_scores.append((word, score))
        
        # Sort by score (descending)
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        return word_scores[:count]
    
    def get_status(self) -> dict:
        """Get current solver status."""
        all_valid_matches = self.get_all_valid_words_matching_constraints()
        
        return {
            'possible_answers_count': len(self.possible_answers),
            'possible_answers': self.possible_answers[:10] if len(self.possible_answers) <= 10 else self.possible_answers[:5],
            'all_valid_matches_count': len(all_valid_matches),
            'all_valid_matches': all_valid_matches[:10] if len(all_valid_matches) <= 10 else all_valid_matches[:5],
            'guessed_words': self.guessed_words,
            'constraints': self.constraints
        }
    
    def reset(self):
        """Reset the solver for a new game."""
        self.possible_answers = self.answers.copy()
        self.guessed_words = []
        self.guess_feedbacks = []
        self.constraints = {
            'correct_positions': {},
            'wrong_positions': {},
            'contains': set(),
            'excludes': set()
        }
        self.history = []  # Clear history on reset

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_board(solver):
    """Print the Wordle board with colored boxes using ANSI escape codes."""
    RESET = '\033[0m'
    # Color schemes: background + foreground
    COLORS = {
        'B': '\033[40m\033[97m',   # Black bg, bright white text
        'G': '\033[42m\033[97m',   # Green bg, bright white text
        'Y': '\033[43m\033[30m',   # Yellow bg, black text
    }
    EMPTY = '\033[90m'  # Gray for empty rows

    max_rows = 6
    print()
    for row in range(max_rows):
        if row < len(solver.guessed_words):
            word = solver.guessed_words[row]
            feedback = solver.guess_feedbacks[row]
            cells = []
            for i in range(5):
                color = COLORS.get(feedback[i], COLORS['B'])
                cells.append(f"{color} {word[i]} {RESET}")
            print("\t" + "".join(cells))
        else:
            print(f"\t{EMPTY}[ ][ ][ ][ ][ ]{RESET}")
    print()


def print_status_line(solver):
    """Print remaining possibilities count below the board."""
    status = solver.get_status()
    print(f"  Remaining: {status['possible_answers_count']} possible answers, {status['all_valid_matches_count']} valid matches")
    if status['possible_answers_count'] <= 10 and status['possible_answers_count'] > 0:
        print(f"  Possibilities: {', '.join(status['possible_answers'])}")


def print_solve_suggestions(solver):
    """Print auto solve suggestions after feedback."""
    all_valid_matches = solver.get_all_valid_words_matching_constraints()

    if len(all_valid_matches) == 1:
        print(f"  The answer is: {all_valid_matches[0]}")
        return

    if len(all_valid_matches) == 0:
        print("  No valid matches remaining!")
        return

    solve_suggestions = solver.get_best_solve_suggestions()
    if not solve_suggestions:
        return

    # Find the highest score and collect all tied words (up to 3)
    top_score = solve_suggestions[0][1]
    tied = [(w, s) for w, s in solve_suggestions if s == top_score]
    tied = tied[:3]

    if len(tied) == 1:
        print(f"  Best suggestion: {tied[0][0]} (score: {tied[0][1]:.1f})")
    else:
        print(f"  Top suggestions (tied at {top_score:.1f}):")
        for w, s in tied:
            print(f"    - {w}")

    # Check for guaranteed solve word when few answers remain
    if 3 <= len(all_valid_matches) <= 8:
        guaranteed_word = solver.find_guaranteed_solve_word()
        if guaranteed_word:
            print(f"  Guaranteed 2-move solve: {guaranteed_word}")


def print_commands():
    """Print the command menu."""
    print("Commands:")
    print("  'g' / 'guess'       - Get best guess suggestions")
    print("  'f' / 'feedback'    - Add feedback (e.g., 'f CRANE BBYGG')")
    print("  'u' / 'undo'        - Undo the last feedback")
    print("  'r' / 'reset'       - Start new game")
    print("  'q' / 'quit'        - Exit")
    print()


def main():
    """Interactive Wordle solver interface."""
    solver = WordleSolver()

    clear_screen()
    print("Wordle Solver")
    print("=" * 40)
    print(f"Loaded {len(solver.answers)} possible answers, {len(solver.valid_words)} valid guess words")
    print()
    print_commands()

    while True:
        command = input(">> ").strip().lower()

        if command in ('quit', 'q'):
            break

        elif command in ('guess', 'g'):
            clear_screen()
            print_status_line(solver)
            print_board(solver)

            suggestions = solver.get_best_guesses(5)
            solve_suggestions = solver.get_best_solve_suggestions()
            all_valid_matches = solver.get_all_valid_words_matching_constraints()

            if len(all_valid_matches) == 1:
                print(f"  The answer is: {all_valid_matches[0]}")
            elif suggestions or solve_suggestions:
                if suggestions:
                    print("  Best guess suggestions:")
                    for i, (word, score) in enumerate(suggestions, 1):
                        print(f"  {i}. {word} (score: {score:.1f})")

                if solve_suggestions:
                    print("\n  Best solve suggestions:")
                    for i, (word, score) in enumerate(solve_suggestions, 1):
                        indicator = " (answer)" if word in solver.answers else ""
                        print(f"  {i}. {word} (score: {score:.1f}){indicator}")

                if 3 <= len(all_valid_matches) <= 8:
                    guaranteed_word = solver.find_guaranteed_solve_word()
                    if guaranteed_word:
                        print(f"\n  Guaranteed 2-move solve: {guaranteed_word}")
            else:
                print("  No valid guesses available!")
            print()
            print_commands()

        elif command.startswith(('feedback ', 'f ')):
            try:
                parts = command.split()
                if len(parts) != 3:
                    clear_screen()
                    print_status_line(solver)
                    print_board(solver)
                    print("  Usage: f <word> <result>")
                    print("  Result format: G=Green, Y=Yellow, B=Black (e.g., f CRANE BBYGG)")
                    print()
                    print_commands()
                    continue

                word = parts[1]
                result = parts[2]
                solver.add_feedback(word, result)

                clear_screen()
                print_status_line(solver)
                print_board(solver)
                print_solve_suggestions(solver)
                print()
                print_commands()

            except ValueError as e:
                clear_screen()
                print_status_line(solver)
                print_board(solver)
                print(f"  Error: {e}")
                print()
                print_commands()

        elif command in ('undo', 'u'):
            if solver.undo_last_feedback():
                clear_screen()
                print_status_line(solver)
                print_board(solver)
                print("  Last feedback undone!")
            else:
                clear_screen()
                print_status_line(solver)
                print_board(solver)
                print("  No feedback to undo!")
            print()
            print_commands()

        elif command in ('reset', 'r'):
            solver.reset()
            clear_screen()
            print_status_line(solver)
            print_board(solver)
            print("  Solver reset for new game!")
            print()
            print_commands()

        else:
            clear_screen()
            print_status_line(solver)
            print_board(solver)
            print(f"  Unknown command: '{command}'")
            print()
            print_commands()

if __name__ == "__main__":
    main()