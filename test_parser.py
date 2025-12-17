"""
Simple test script to verify the descriptive notation parser works correctly.
Run this after installing python-chess to test basic functionality.

Aaron Beckley December 17, 2025

"""

from chess import Board
from descriptive_notation_parser import DescriptiveNotationParser


def test_basic_moves():
    """Test basic descriptive notation moves."""
    board = Board()
    parser = DescriptiveNotationParser(board)
    
    # Test some common opening moves
    test_cases = [
        ("P-K4", "e2e4"),  # White pawn to e4
        ("P-K4", "e7e5"),  # Black pawn to e5 (after white moves)
        ("N-KB3", "g1f3"),  # White knight to f3
        ("P-Q4", "d2d4"),  # White pawn to d4
    ]
    
    print("Testing basic moves...")
    for notation, expected_uci in test_cases:
        move = parser.parse(notation)
        if move:
            actual_uci = move.uci()
            status = "✓" if actual_uci == expected_uci else "✗"
            print(f"{status} {notation:10} -> {actual_uci} (expected: {expected_uci})")
        else:
            print(f"✗ {notation:10} -> Failed to parse")
        
        # Make the move to test next one from black's perspective
        if move and move in board.legal_moves:
            board.push(move)
            parser = DescriptiveNotationParser(board)


def test_castling():
    """Test castling moves."""
    # Create a position where castling is possible
    board = Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    parser = DescriptiveNotationParser(board)
    
    print("\nTesting castling...")
    move = parser.parse("O-O")
    if move:
        print(f"✓ O-O -> {move.uci()}")
    else:
        print("✗ O-O -> Failed to parse")


if __name__ == "__main__":
    try:
        test_basic_moves()
        test_castling()
        print("\nTests completed!")
    except ImportError:
        print("Error: python-chess not installed. Run: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error during testing: {e}")

