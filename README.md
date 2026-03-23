# WordleSolver

An interactive CLI Wordle solver that suggests optimal guesses based on letter frequency analysis and constraint filtering.

## Features

- Visual Wordle board with colored tiles (green, yellow, black) matching game feedback
- Ranked guess and solve suggestions scored by letter frequency
- Guaranteed 2-move solve detection when few possibilities remain
- Undo/reset support for correcting mistakes
- Uses two word lists: possible answers and all valid guess words

## Requirements

- Python 3.6+
- `answers-wordlist.txt` - list of possible Wordle answers (5-letter words, one per line)
- `valid-words.txt` - list of all valid guess words (5-letter words, one per line)

## How to Run

```bash
python3 solver.py
```

## Build Executable

To build a standalone executable with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "answers-wordlist.txt:." --add-data "valid-words.txt:." solver.py
```

The executable will be at `dist/solver`. On Windows, use `;` instead of `:` as the separator:

```bash
pyinstaller --onefile --add-data "answers-wordlist.txt;." --add-data "valid-words.txt;." solver.py
```

## Usage

| Command | Short | Description |
|---------|-------|-------------|
| `guess` | `g` | Show best guess and solve suggestions |
| `feedback <word> <result>` | `f <word> <result>` | Submit a guess with its feedback |
| `undo` | `u` | Undo the last feedback |
| `reset` | `r` | Start a new game |
| `quit` | `q` | Exit the solver |

### Feedback Format

The result string uses 5 characters, one per letter position:

- `G` = Green (correct letter, correct position)
- `Y` = Yellow (correct letter, wrong position)
- `B` = Black (letter not in the word)

### Example Session

```
>> f crane bbygg
>> f singe ybbbg
>> g
```

After each feedback command, the solver displays:
1. Remaining possibilities count
2. The board with colored tiles reflecting your guesses
3. Top solve suggestions (up to 3 if tied at the highest score)
