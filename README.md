# Chess Board Simulator - Descriptive Notation

A Python GUI application for playing chess using Descriptive Notation. This application provides a visual chess board interface where you can input moves using traditional Descriptive Notation.




## Features

- **Visual Chess Board**: Interactive 8x8 chess board with Unicode piece symbols
- **Descriptive Notation Support**: Input moves using traditional descriptive notation
- **Move Validation**: Validates moves against chess rules
- **Move History**: Tracks and displays move history
- **Undo Functionality**: Undo moves to go back in the game
- **Game Status**: Detects check, checkmate, stalemate, and draws

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python chess_board_gui.py
```

## Descriptive Notation Guide

Descriptive notation uses relative positions from each player's perspective:

### Files (from each player's perspective):
- **QR** = Queen's Rook file (a-file for White, h-file for Black)
- **QN** = Queen's Knight file (b-file for White, g-file for Black)
- **QB** = Queen's Bishop file (c-file for White, f-file for Black)
- **Q** = Queen file (d-file for White, d-file for Black)
- **K** = King file (e-file for White, e-file for Black)
- **KB** = King's Bishop file (f-file for White, c-file for Black)
- **KN** = King's Knight file (g-file for White, b-file for Black)
- **KR** = King's Rook file (h-file for White, a-file for Black)

### Ranks:
- Ranks 1-8 are numbered from each player's perspective
- For White: Rank 1 is the bottom, Rank 8 is the top
- For Black: Rank 1 is the top, Rank 8 is the bottom

### Piece Notation:
- **P** = Pawn
- **R** = Rook
- **N** = Knight
- **B** = Bishop
- **Q** = Queen
- **K** = King

### Examples:

- `P-K4` - Pawn to King's 4th square
- `N-KB3` - Knight to King's Bishop's 3rd square
- `R-QN1` - Rook to Queen's Knight's 1st square
- `O-O` - Castling kingside
- `O-O-O` - Castling queenside
- `PxP` - Pawn takes pawn
- `NxP` - Knight takes pawn
- `P-K8(Q)` - Pawn promotes to Queen on King's 8th

### Special Indicators:
- `x` or `X` - Capture
- `ch` or `+` - Check
- `mate` or `#` - Checkmate

## How to Use

1. **Enter Moves**: Type moves in descriptive notation in the input field and press Enter or click "Make Move"
2. **Click Board**: You can also click pieces on the board to select them, then click the destination square
3. **View History**: All moves are displayed in the move history panel
4. **Undo Moves**: Click "Undo Move" to go back one move
5. **Reset Board**: Click "Reset Board" to start a new game

## Improvements Over Standard Implementations

This implementation includes several improvements for handling descriptive notation:

- Better handling of generic captures (PxP, NxP, etc.)
- Improved disambiguation when multiple pieces can move to the same square
- More robust parsing of file and rank combinations
- Proper handling of pawn moves and promotions
- Better error messages for invalid moves

## Files

- `chess_board_gui.py` - Main GUI application
- `descriptive_notation_parser.py` - Parser for converting descriptive notation to chess moves
- `requirements.txt` - Python dependencies

## License

This project is provided as-is for educational and personal use.

