"""
Descriptive Notation Parser for Chess

Descriptive notation uses relative positions from each player's perspective:
- Files: QR, QN, QB, Q, K, KB, KN, KR (Queen's Rook to King's Rook)
- Ranks: 1-8 (from each player's perspective)
- Pieces: P (Pawn), R (Rook), N (Knight), B (Bishop), Q (Queen), K (King)
- Special moves: O-O (castling kingside), O-O-O (castling queenside)
- Captures: x
- Check: ch or +
- Checkmate: mate or #
- Pawn promotion: e.g., P-K8(Q)

Aaron Beckley December 17, 2025

"""

import re
from typing import Optional, Tuple
from chess import Board, Move, Square


class DescriptiveNotationParser:
    """Parser for converting Descriptive Notation to standard chess moves."""
    
    # File mapping: Descriptive -> Standard (a-h)
    FILE_MAP = {
        'QR': 'a', 'QN': 'b', 'QB': 'c', 'Q': 'd',
        'K': 'e', 'KB': 'f', 'KN': 'g', 'KR': 'h'
    }
    
    # Abbreviated file names (ambiguous - could be Q-side or K-side)
    AMBIGUOUS_FILES = {
        'R': ['a', 'h'],   # QR or KR
        'N': ['b', 'g'],   # QN or KN  
        'B': ['c', 'f'],   # QB or KB
    }
    
    # Reverse mapping
    FILE_REVERSE = {v: k for k, v in FILE_MAP.items()}
    
    # Piece symbols
    PIECE_SYMBOLS = {
        'P': None,  # Pawn (no symbol in standard)
        'R': 'R', 'N': 'N', 'B': 'B', 'Q': 'Q', 'K': 'K'
    }
    
    # Qualified piece names (specify which of two pieces)
    # QR = Queen's Rook, KR = King's Rook, etc.
    QUALIFIED_PIECES = {
        'QR': ('R', 'Q'),  # Rook on queenside
        'KR': ('R', 'K'),  # Rook on kingside
        'QN': ('N', 'Q'),  # Knight on queenside
        'KN': ('N', 'K'),  # Knight on kingside
        'QB': ('B', 'Q'),  # Bishop on queenside
        'KB': ('B', 'K'),  # Bishop on kingside
    }
    
    def __init__(self, board: Board):
        self.board = board
        self.is_white_turn = board.turn
    
    def parse(self, notation: str) -> Optional[Move]:
        """
        Parse descriptive notation and return a Move object.
        
        Examples:
        - P-K4 (pawn to king's 4th)
        - N-KB3 (knight to king's bishop's 3rd)
        - R-QN1 (rook to queen's knight's 1st)
        - O-O (castling kingside)
        - O-O-O (castling queenside)
        - PxP (pawn takes pawn)
        - NxP (knight takes pawn)
        """
        notation = notation.strip().upper()
        
        # Remove check/checkmate indicators and en passant notation
        notation = re.sub(r'\s*(ch|check|\+|mate|#|e\.?\s*p\.?).*$', '', notation, flags=re.IGNORECASE)
        
        # Handle castling
        if notation == 'O-O' or notation == '0-0':
            return self._parse_castling_kingside()
        if notation == 'O-O-O' or notation == '0-0-0':
            return self._parse_castling_queenside()
        
        # Handle pawn promotion
        if '(' in notation and ')' in notation:
            return self._parse_promotion(notation)
        
        # Check for qualified piece names first (QR, KR, QN, KN, QB, KB)
        # These must be followed by - or x to be piece moves (e.g., QR-K1, KN-B3)
        for qualified in ['QR', 'KR', 'QN', 'KN', 'QB', 'KB']:
            if notation.startswith(qualified):
                if len(notation) > 2 and notation[2] in ['-', 'x', 'X']:
                    return self._parse_qualified_piece_move(notation)
                # Otherwise it's a pawn move to that file (e.g., QR4 = pawn to QR4)
                break
        
        # Parse piece moves (non-pawn pieces)
        # Check for explicit piece notation: R, N, B, Q, or K followed by - or x
        if notation.startswith(('R', 'N', 'B', 'Q')):
            return self._parse_piece_move(notation)
        elif notation.startswith('K'):
            # Could be King move (K-K2, KxP) or pawn to K file (K4, P-K4)
            # King moves typically have K- or Kx, pawn moves have just K followed by number
            if len(notation) > 1 and notation[1] in ['-', 'x', 'X']:
                # Likely a king move
                return self._parse_piece_move(notation)
            elif notation.startswith(('KB', 'KN', 'KR')):
                # These are file names, not king moves - treat as pawn move
                return self._parse_pawn_move(notation)
            else:
                # Could be either - try king first, then pawn
                king_move = self._parse_piece_move(notation)
                if king_move:
                    return king_move
                return self._parse_pawn_move(notation)
        else:
            # Assume it's a pawn move (P-K4, K4, etc.)
            return self._parse_pawn_move(notation)
    
    def _parse_castling_kingside(self) -> Optional[Move]:
        """Parse kingside castling."""
        if self.is_white_turn:
            if self.board.has_kingside_castling_rights(True):
                return Move.from_uci('e1g1')
        else:
            if self.board.has_kingside_castling_rights(False):
                return Move.from_uci('e8g8')
        return None
    
    def _parse_castling_queenside(self) -> Optional[Move]:
        """Parse queenside castling."""
        if self.is_white_turn:
            if self.board.has_queenside_castling_rights(True):
                return Move.from_uci('e1c1')
        else:
            if self.board.has_queenside_castling_rights(False):
                return Move.from_uci('e8c8')
        return None
    
    def _parse_promotion(self, notation: str) -> Optional[Move]:
        """Parse pawn promotion moves like P-K8(Q)."""
        match = re.match(r'P-([A-Z]+)(\d+)\(([QRBN])\)', notation)
        if not match:
            return None
        
        file_desc, rank_desc, promo_piece = match.groups()
        target_file = self._descriptive_file_to_standard(file_desc)
        target_rank = self._descriptive_rank_to_standard(int(rank_desc))
        
        if target_file is None or target_rank is None:
            return None
        
        target_square = self._file_rank_to_square(target_file, target_rank)
        
        # Find the pawn that can move to this square
        for move in self.board.legal_moves:
            if move.to_square == target_square and move.promotion:
                promo_map = {'Q': 5, 'R': 4, 'B': 3, 'N': 2}
                if move.promotion == promo_map.get(promo_piece):
                    return move
        
        return None
    
    def _parse_piece_move(self, notation: str) -> Optional[Move]:
        """Parse piece moves like N-KB3, R-QN1, Q-N3, RxP, etc."""
        # Extract piece type
        piece_char = notation[0]
        notation = notation[1:]
        
        is_capture = 'x' in notation or 'X' in notation
        notation = notation.replace('-', '').replace('x', '').replace('X', '')
        
        # Handle captures like NxP, NxB, RxR - where captured piece type is specified
        if notation in ['P', 'R', 'N', 'B', 'Q', 'K', '']:
            # Capture of a specific piece type (or any capture if empty)
            captured_type = notation if notation else None
            return self._parse_generic_capture(piece_char, captured_type)
        
        # Parse file and rank
        file_desc = None
        rank_desc = None
        ambiguous_file = None
        
        # Try to match file patterns (longest first to avoid partial matches)
        for file_pattern in ['QR', 'QN', 'QB', 'KR', 'KN', 'KB', 'Q', 'K']:
            if notation.startswith(file_pattern):
                file_desc = file_pattern
                notation = notation[len(file_pattern):]
                break
        
        # If no standard file found, check for ambiguous abbreviated files (R, N, B)
        if file_desc is None:
            for abbrev in ['R', 'N', 'B']:
                if notation.startswith(abbrev):
                    ambiguous_file = abbrev
                    notation = notation[1:]
                    break
        
        # Extract rank (should be a digit)
        rank_match = re.search(r'(\d+)', notation)
        if rank_match:
            rank_desc = int(rank_match.group(1))
        
        if (file_desc is None and ambiguous_file is None) or rank_desc is None:
            return None
        
        # Find the piece that can move to this square
        piece_map = {'P': 1, 'R': 4, 'N': 2, 'B': 3, 'Q': 5, 'K': 6}
        piece_type = piece_map.get(piece_char)
        
        if piece_type is None:
            return None
        
        target_rank = self._descriptive_rank_to_standard(rank_desc)
        if target_rank is None:
            return None
        
        # If we have an ambiguous file, try both possibilities
        if ambiguous_file:
            possible_files = self.AMBIGUOUS_FILES.get(ambiguous_file, [])
            all_candidates = []
            
            for target_file in possible_files:
                target_square = self._file_rank_to_square(target_file, target_rank)
                
                for move in self.board.legal_moves:
                    if move.to_square == target_square:
                        piece = self.board.piece_at(move.from_square)
                        if piece and piece.piece_type == piece_type and piece.color == self.board.turn:
                            all_candidates.append(move)
            
            if len(all_candidates) == 1:
                return all_candidates[0]
            elif len(all_candidates) > 1:
                if is_capture:
                    for move in all_candidates:
                        if self.board.piece_at(move.to_square):
                            return move
                return all_candidates[0]
            return None
        
        # Standard file handling
        target_file = self._descriptive_file_to_standard(file_desc)
        if target_file is None:
            return None
        
        target_square = self._file_rank_to_square(target_file, target_rank)
        
        legal_moves = list(self.board.legal_moves)
        
        # Filter by target square and piece type
        candidates = []
        for move in legal_moves:
            if move.to_square == target_square:
                piece = self.board.piece_at(move.from_square)
                if piece and piece.piece_type == piece_type and piece.color == self.board.turn:
                    candidates.append(move)
        
        # If multiple candidates, try to disambiguate
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            # If multiple pieces can move, prefer the one that makes sense
            # (e.g., if it's a capture, prefer the one that captures)
            if is_capture:
                # Prefer moves that actually capture
                for move in candidates:
                    if self.board.piece_at(move.to_square):
                        return move
            # Return first valid move if can't disambiguate
            return candidates[0]
        
        return None
    
    def _parse_qualified_piece_move(self, notation: str) -> Optional[Move]:
        """
        Parse qualified piece moves like QR-K1, KN-B3, KB-Q2, etc.
        The qualifier (Q or K) specifies which of two pieces to move.
        """
        # Extract qualified piece name (first 2 characters)
        qualified_name = notation[:2]
        notation = notation[2:]
        
        piece_info = self.QUALIFIED_PIECES.get(qualified_name)
        if not piece_info:
            return None
        
        piece_char, side_qualifier = piece_info  # e.g., ('R', 'Q') for QR
        
        is_capture = 'x' in notation or 'X' in notation
        notation = notation.replace('-', '').replace('x', '').replace('X', '')
        
        # Handle generic captures like QRxP
        if notation == 'P' or notation == '':
            return self._parse_qualified_capture(piece_char, side_qualifier)
        
        # Parse destination file and rank
        file_desc = None
        rank_desc = None
        ambiguous_file = None
        
        # Try to match file patterns (longest first)
        for file_pattern in ['QR', 'QN', 'QB', 'KR', 'KN', 'KB', 'Q', 'K']:
            if notation.startswith(file_pattern):
                file_desc = file_pattern
                notation = notation[len(file_pattern):]
                break
        
        # If no standard file found, check for ambiguous abbreviated files
        if file_desc is None:
            for abbrev in ['R', 'N', 'B']:
                if notation.startswith(abbrev):
                    ambiguous_file = abbrev
                    notation = notation[1:]
                    break
        
        # Extract rank
        rank_match = re.search(r'(\d+)', notation)
        if rank_match:
            rank_desc = int(rank_match.group(1))
        
        if (file_desc is None and ambiguous_file is None) or rank_desc is None:
            return None
        
        piece_map = {'P': 1, 'R': 4, 'N': 2, 'B': 3, 'Q': 5, 'K': 6}
        piece_type = piece_map.get(piece_char)
        if piece_type is None:
            return None
        
        target_rank = self._descriptive_rank_to_standard(rank_desc)
        if target_rank is None:
            return None
        
        # Get all possible target squares
        target_squares = []
        if ambiguous_file:
            possible_files = self.AMBIGUOUS_FILES.get(ambiguous_file, [])
            for f in possible_files:
                target_squares.append(self._file_rank_to_square(f, target_rank))
        else:
            target_file = self._descriptive_file_to_standard(file_desc)
            if target_file:
                target_squares.append(self._file_rank_to_square(target_file, target_rank))
        
        if not target_squares:
            return None
        
        # Find all candidate moves for this piece type to any target square
        candidates = []
        for move in self.board.legal_moves:
            if move.to_square in target_squares:
                piece = self.board.piece_at(move.from_square)
                if piece and piece.piece_type == piece_type and piece.color == self.board.turn:
                    candidates.append(move)
        
        if len(candidates) == 0:
            return None
        elif len(candidates) == 1:
            return candidates[0]
        
        # Multiple candidates - use the side qualifier to disambiguate
        # Queenside pieces are on files a-d (indices 0-3)
        # Kingside pieces are on files e-h (indices 4-7)
        for move in candidates:
            from_file = move.from_square % 8  # 0-7 for a-h
            if side_qualifier == 'Q' and from_file <= 3:  # Queenside (a-d)
                return move
            elif side_qualifier == 'K' and from_file >= 4:  # Kingside (e-h)
                return move
        
        # If no exact match, just return first candidate
        return candidates[0]
    
    def _parse_qualified_capture(self, piece_char: str, side_qualifier: str) -> Optional[Move]:
        """Parse qualified captures like QRxP, KNxB where target isn't fully specified."""
        piece_map = {'P': 1, 'R': 4, 'N': 2, 'B': 3, 'Q': 5, 'K': 6}
        piece_type = piece_map.get(piece_char)
        
        if piece_type is None:
            return None
        
        # Find all capture moves for this piece type
        candidates = []
        for move in self.board.legal_moves:
            piece = self.board.piece_at(move.from_square)
            captured = self.board.piece_at(move.to_square)
            if (piece and piece.piece_type == piece_type and 
                piece.color == self.board.turn and captured):
                candidates.append(move)
        
        if len(candidates) == 0:
            return None
        elif len(candidates) == 1:
            return candidates[0]
        
        # Multiple candidates - use side qualifier to disambiguate
        for move in candidates:
            from_file = move.from_square % 8
            if side_qualifier == 'Q' and from_file <= 3:
                return move
            elif side_qualifier == 'K' and from_file >= 4:
                return move
        
        return candidates[0]
    
    def _parse_generic_capture(self, piece_char: str, captured_type: Optional[str] = None) -> Optional[Move]:
        """
        Parse generic captures like NxP, NxB, RxR where target isn't a square.
        captured_type: optional piece type being captured (P, R, N, B, Q, K)
        """
        piece_map = {'P': 1, 'R': 4, 'N': 2, 'B': 3, 'Q': 5, 'K': 6}
        piece_type = piece_map.get(piece_char)
        target_piece_type = piece_map.get(captured_type) if captured_type else None
        
        if piece_type is None:
            return None
        
        legal_moves = list(self.board.legal_moves)
        
        # Find all capture moves for this piece type
        candidates = []
        for move in legal_moves:
            piece = self.board.piece_at(move.from_square)
            captured = self.board.piece_at(move.to_square)
            if (piece and piece.piece_type == piece_type and 
                piece.color == self.board.turn and captured):
                # If target piece type specified, filter by it
                if target_piece_type is None or captured.piece_type == target_piece_type:
                    candidates.append(move)
        
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            # Return first capture move
            return candidates[0]
        
        return None
    
    def _parse_pawn_move(self, notation: str) -> Optional[Move]:
        """Parse pawn moves like P-K4, PxP, P-KB4, P-N4, etc."""
        # Remove P- prefix if present
        if notation.startswith('P-'):
            notation = notation[2:]
        elif notation.startswith('P'):
            notation = notation[1:]
        
        is_capture = 'x' in notation or 'X' in notation
        
        # Handle generic pawn captures: PxP, PxN, PxB, PxR, PxQ
        remaining = notation.replace('x', '').replace('X', '')
        if remaining in ['P', 'N', 'B', 'R', 'Q', '']:
            captured_type = remaining if remaining else None
            return self._parse_generic_capture('P', captured_type)
        
        notation = notation.replace('x', '').replace('X', '')
        
        # Extract file and rank
        file_desc = None
        rank_desc = None
        ambiguous_file = None
        
        # Try to match file patterns (longest first)
        for file_pattern in ['QR', 'QN', 'QB', 'KR', 'KN', 'KB', 'Q', 'K']:
            if notation.startswith(file_pattern):
                file_desc = file_pattern
                notation = notation[len(file_pattern):]
                break
        
        # If no standard file found, check for ambiguous abbreviated files (R, N, B)
        if file_desc is None:
            for abbrev in ['R', 'N', 'B']:
                if notation.startswith(abbrev):
                    ambiguous_file = abbrev
                    notation = notation[1:]
                    break
        
        # Extract rank
        rank_match = re.search(r'(\d+)', notation)
        if rank_match:
            rank_desc = int(rank_match.group(1))
        
        if (file_desc is None and ambiguous_file is None) or rank_desc is None:
            return None
        
        target_rank = self._descriptive_rank_to_standard(rank_desc)
        if target_rank is None:
            return None
        
        # If we have an ambiguous file, try both possibilities
        if ambiguous_file:
            possible_files = self.AMBIGUOUS_FILES.get(ambiguous_file, [])
            all_candidates = []
            
            for target_file in possible_files:
                target_square = self._file_rank_to_square(target_file, target_rank)
                
                for move in self.board.legal_moves:
                    if move.to_square == target_square:
                        piece = self.board.piece_at(move.from_square)
                        if piece and piece.piece_type == 1 and piece.color == self.board.turn:
                            all_candidates.append(move)
            
            if len(all_candidates) == 1:
                return all_candidates[0]
            elif len(all_candidates) > 1:
                if is_capture:
                    for move in all_candidates:
                        if self.board.piece_at(move.to_square):
                            return move
                return all_candidates[0]
            return None
        
        # Standard file handling
        target_file = self._descriptive_file_to_standard(file_desc)
        if target_file is None:
            return None
        
        target_square = self._file_rank_to_square(target_file, target_rank)
        
        # Find pawn moves to this square
        legal_moves = list(self.board.legal_moves)
        candidates = []
        for move in legal_moves:
            if move.to_square == target_square:
                piece = self.board.piece_at(move.from_square)
                if piece and piece.piece_type == 1 and piece.color == self.board.turn:  # Pawn
                    candidates.append(move)
        
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            # If multiple pawns can move, prefer capture if it's a capture
            if is_capture:
                for move in candidates:
                    if self.board.piece_at(move.to_square):
                        return move
            return candidates[0]
        
        return None
    
    def _descriptive_file_to_standard(self, file_desc: str) -> Optional[str]:
        """Convert descriptive file to standard file (a-h)."""
        return self.FILE_MAP.get(file_desc)
    
    def _descriptive_rank_to_standard(self, rank_desc: int) -> Optional[int]:
        """
        Convert descriptive rank to standard rank (0-7).
        In descriptive notation, ranks are from each player's perspective.
        """
        if self.is_white_turn:
            # White's perspective: rank 1 is bottom (rank 0), rank 8 is top (rank 7)
            return rank_desc - 1
        else:
            # Black's perspective: rank 1 is top (rank 7), rank 8 is bottom (rank 0)
            return 8 - rank_desc
    
    def _file_rank_to_square(self, file: str, rank: int) -> Square:
        """Convert file (a-h) and rank (0-7) to Square."""
        file_idx = ord(file) - ord('a')
        return Square(rank * 8 + file_idx)

