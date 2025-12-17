"""
Chess Board GUI with Descriptive Notation Support

A Python GUI application for playing chess using Descriptive Notation.

Aaron Beckley December 17, 2025

"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional
from chess import Board, Move, Piece, SQUARES, square_name, PIECE_NAMES
from descriptive_notation_parser import DescriptiveNotationParser


class MoveToDescriptive:
    """Convert chess moves to descriptive notation."""
    
    # File names in descriptive notation
    FILE_NAMES = {
        0: 'QR', 1: 'QN', 2: 'QB', 3: 'Q',
        4: 'K', 5: 'KB', 6: 'KN', 7: 'KR'
    }
    
    PIECE_LETTERS = {1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K'}
    
    @classmethod
    def convert(cls, board: Board, move: Move) -> str:
        """Convert a move to descriptive notation."""
        # Handle castling
        if board.is_castling(move):
            if board.is_kingside_castling(move):
                return "O-O"
            else:
                return "O-O-O"
        
        from_sq = move.from_square
        to_sq = move.to_square
        piece = board.piece_at(from_sq)
        captured = board.piece_at(to_sq)
        
        if piece is None:
            return move.uci()
        
        # Get piece letter
        piece_letter = cls.PIECE_LETTERS.get(piece.piece_type, '')
        
        # Get destination in descriptive notation
        to_file = to_sq % 8
        to_rank = to_sq // 8
        
        # Rank is from the player's perspective
        if piece.color:  # White
            rank_num = to_rank + 1
        else:  # Black
            rank_num = 8 - to_rank
        
        file_name = cls.FILE_NAMES[to_file]
        
        # Build the move string
        if captured:
            # Capture
            if piece.piece_type == 1:  # Pawn
                # For pawn captures, show the file
                from_file = from_sq % 8
                from_file_name = cls.FILE_NAMES[from_file]
                result = f"{from_file_name}Px{file_name}{rank_num}"
            else:
                result = f"{piece_letter}x{file_name}{rank_num}"
        else:
            # Regular move
            result = f"{piece_letter}-{file_name}{rank_num}"
        
        # Handle promotion
        if move.promotion:
            promo_letter = cls.PIECE_LETTERS.get(move.promotion, '')
            result += f"({promo_letter})"
        
        return result


class ChessBoardGUI:
    """Main GUI application for chess board with descriptive notation."""
    
    SQUARE_SIZE = 64
    BOARD_SIZE = SQUARE_SIZE * 8
    
    # Colors
    LIGHT_SQUARE = '#f0d9b5'
    DARK_SQUARE = '#b58863'
    HIGHLIGHT_SQUARE = '#aaa23a'
    
    # Unicode chess pieces
    PIECES = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    }
    
    PIECE_TYPES = ['K', 'Q', 'R', 'B', 'N', 'P']
    
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Board - Descriptive Notation")
        self.root.configure(bg='#2b2b2b')
        
        # Board state
        self.board = Board()
        self.move_history = []  # List of FENs before each move
        self.move_notations = []  # Descriptive notation strings
        self.board_states = [Board().fen()]  # All board states including initial
        self.current_move_index = 0  # Which move we're viewing (0 = start position)
        
        # Animation state
        self.animation_duration = 200  # milliseconds
        self.animation_steps = 15
        self.animating = False
        
        # Drag state
        self.drag_data = {"piece": None, "from_square": None, "item": None, "is_white": None}
        
        self._setup_styles()
        self._create_ui()
        self._draw_board()
        self._draw_sidebar()
    
    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white')
        style.configure('TLabelframe', background='#2b2b2b', foreground='white')
        style.configure('TLabelframe.Label', background='#2b2b2b', foreground='white')
    
    def _create_ui(self):
        """Create the user interface."""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left: Piece palette
        self._create_sidebar()
        
        # Center: Chess board
        self._create_board()
        
        # Right: Controls
        self._create_controls()
    
    def _create_sidebar(self):
        """Create the piece palette sidebar."""
        sidebar = ttk.Frame(self.main_frame)
        sidebar.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
        
        # Black pieces
        ttk.Label(sidebar, text="Black", font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        self.black_canvas = tk.Canvas(sidebar, width=60, height=200, bg='#3c3c3c', 
                                       highlightthickness=0)
        self.black_canvas.pack(pady=5)
        
        # White pieces
        ttk.Label(sidebar, text="White", font=('Arial', 12, 'bold')).pack(pady=(15, 5))
        self.white_canvas = tk.Canvas(sidebar, width=60, height=200, bg='#3c3c3c',
                                       highlightthickness=0)
        self.white_canvas.pack(pady=5)
        
        # Bind sidebar events - need drag and release too
        self.black_canvas.bind('<Button-1>', lambda e: self._sidebar_press(e, False))
        self.black_canvas.bind('<B1-Motion>', self._sidebar_drag)
        self.black_canvas.bind('<ButtonRelease-1>', self._on_release)
        
        self.white_canvas.bind('<Button-1>', lambda e: self._sidebar_press(e, True))
        self.white_canvas.bind('<B1-Motion>', self._sidebar_drag)
        self.white_canvas.bind('<ButtonRelease-1>', self._on_release)
    
    def _create_board(self):
        """Create the chess board canvas."""
        board_frame = ttk.Frame(self.main_frame)
        board_frame.pack(side=tk.LEFT, padx=10)
        
        # Main board canvas
        self.board_canvas = tk.Canvas(
            board_frame,
            width=self.BOARD_SIZE,
            height=self.BOARD_SIZE,
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.board_canvas.pack()
        
        # File labels
        file_frame = ttk.Frame(board_frame)
        file_frame.pack(fill=tk.X)
        for i, f in enumerate('abcdefgh'):
            lbl = ttk.Label(file_frame, text=f, font=('Arial', 10), width=2, anchor='center')
            lbl.pack(side=tk.LEFT, expand=True)
        
        # Bind board events
        self.board_canvas.bind('<Button-1>', self._on_click)
        self.board_canvas.bind('<B1-Motion>', self._on_drag)
        self.board_canvas.bind('<ButtonRelease-1>', self._on_release)
        self.board_canvas.bind('<Button-3>', self._on_right_click)
    
    def _create_controls(self):
        """Create the control panel."""
        controls = ttk.Frame(self.main_frame)
        controls.pack(side=tk.LEFT, padx=(10, 0), fill=tk.Y)
        
        # Turn indicator
        self.turn_label = ttk.Label(controls, text="White to move", font=('Arial', 14, 'bold'))
        self.turn_label.pack(pady=10)
        
        # Move input
        input_frame = ttk.LabelFrame(controls, text="Descriptive Notation", padding=10)
        input_frame.pack(fill=tk.X, pady=10)
        
        self.move_entry = ttk.Entry(input_frame, width=20, font=('Courier', 12))
        self.move_entry.pack(fill=tk.X, pady=5)
        self.move_entry.bind('<Return>', lambda e: self._execute_move())
        
        ttk.Label(input_frame, text="e.g. P-K4, N-KB3, O-O", 
                  font=('Arial', 9), foreground='gray').pack()
        
        # History
        history_frame = ttk.LabelFrame(controls, text="Move History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Navigation buttons
        nav_frame = ttk.Frame(history_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.btn_start = ttk.Button(nav_frame, text="⏮", width=3, command=self._go_to_start)
        self.btn_start.pack(side=tk.LEFT, padx=2)
        
        self.btn_back = ttk.Button(nav_frame, text="◀", width=3, command=self._go_back)
        self.btn_back.pack(side=tk.LEFT, padx=2)
        
        self.move_label = ttk.Label(nav_frame, text="Start", font=('Arial', 10), width=10, anchor='center')
        self.move_label.pack(side=tk.LEFT, padx=5, expand=True)
        
        self.btn_forward = ttk.Button(nav_frame, text="▶", width=3, command=self._go_forward)
        self.btn_forward.pack(side=tk.LEFT, padx=2)
        
        self.btn_end = ttk.Button(nav_frame, text="⏭", width=3, command=self._go_to_end)
        self.btn_end.pack(side=tk.LEFT, padx=2)
        
        self.history_text = tk.Text(history_frame, width=25, height=18, 
                                     font=('Courier', 10), bg='#3c3c3c', fg='white',
                                     relief=tk.FLAT)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        self.history_text.config(state=tk.DISABLED)
        
        # Configure tag for highlighted move
        self.history_text.tag_configure('highlight', background='#4a90d9', foreground='white')
        
        # Buttons
        btn_frame = ttk.Frame(controls)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Reset", command=self._reset_board).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Undo", command=self._undo_move).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", command=self._clear_board).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Switch Turn", command=self._switch_turn).pack(side=tk.LEFT, padx=2)
        
        # Status
        self.status_label = ttk.Label(controls, text="Drag pieces to place them", 
                                       font=('Arial', 9), foreground='#888')
        self.status_label.pack(pady=5)
    
    def _draw_sidebar(self):
        """Draw pieces in the sidebars."""
        # Black pieces - dark colored with light outline
        self.black_canvas.delete('all')
        for i, pt in enumerate(self.PIECE_TYPES):
            y = i * 32 + 20
            symbol = self.PIECES[pt.lower()]
            # Draw outline
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                self.black_canvas.create_text(30+dx, y+dy, text=symbol,
                    font=('Arial', 24), fill='#888')
            # Draw piece in dark color
            self.black_canvas.create_text(30, y, text=symbol,
                                           font=('Arial', 24), fill='#1a1a2e',
                                           tags=f'piece_{pt.lower()}')
        
        # White pieces - light colored with dark outline
        self.white_canvas.delete('all')
        for i, pt in enumerate(self.PIECE_TYPES):
            y = i * 32 + 20
            symbol = self.PIECES[pt]
            # Draw outline
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                self.white_canvas.create_text(30+dx, y+dy, text=symbol,
                    font=('Arial', 24), fill='#1a1a2e')
            # Draw piece in light color
            self.white_canvas.create_text(30, y, text=symbol,
                                           font=('Arial', 24), fill='#f5f5f5',
                                           tags=f'piece_{pt}')
    
    def _draw_board(self):
        """Draw the chess board and pieces."""
        self.board_canvas.delete('all')
        
        # Draw squares
        for rank in range(8):
            for file in range(8):
                x1 = file * self.SQUARE_SIZE
                y1 = (7 - rank) * self.SQUARE_SIZE  # Flip so white is at bottom
                x2 = x1 + self.SQUARE_SIZE
                y2 = y1 + self.SQUARE_SIZE
                
                # Alternate colors (a1 should be dark, so when rank+file is even, it's dark)
                color = self.DARK_SQUARE if (rank + file) % 2 == 0 else self.LIGHT_SQUARE
                
                # Highlight if this square is involved in drag
                square = rank * 8 + file
                if self.drag_data["from_square"] == square:
                    color = self.HIGHLIGHT_SQUARE
                
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, 
                                                    outline='', tags=f'sq_{square}')
        
        # Draw pieces
        for square in SQUARES:
            piece = self.board.piece_at(square)
            if piece and square != self.drag_data["from_square"]:
                file = square % 8
                rank = square // 8
                x = file * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                y = (7 - rank) * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                
                symbol = self.PIECES[piece.symbol()]
                # White pieces = light color, Black pieces = dark color
                color = '#f5f5f5' if piece.color else '#1a1a2e'
                
                # Draw piece with outline for visibility
                for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                    outline_color = '#1a1a2e' if piece.color else '#f5f5f5'
                    self.board_canvas.create_text(x+dx, y+dy, text=symbol,
                                                   font=('Arial', 40), fill=outline_color)
                
                self.board_canvas.create_text(x, y, text=symbol, font=('Arial', 40),
                                               fill=color, tags=f'piece_{square}')
        
        # Draw rank labels on left side
        for rank in range(8):
            y = (7 - rank) * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            self.board_canvas.create_text(10, y, text=str(rank + 1), 
                                           font=('Arial', 10, 'bold'), fill='#666')
    
    def _coords_to_square(self, x, y):
        """Convert canvas coordinates to chess square index."""
        file = int(x // self.SQUARE_SIZE)
        rank = 7 - int(y // self.SQUARE_SIZE)
        if 0 <= file < 8 and 0 <= rank < 8:
            return rank * 8 + file
        return None
    
    def _square_to_coords(self, square):
        """Convert chess square index to canvas center coordinates."""
        file = square % 8
        rank = square // 8
        x = file * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
        y = (7 - rank) * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
        return x, y
    
    def _sidebar_press(self, event, is_white):
        """Handle press on sidebar piece."""
        index = int(event.y // 32)
        if 0 <= index < len(self.PIECE_TYPES):
            piece_type = self.PIECE_TYPES[index]
            piece_symbol = piece_type if is_white else piece_type.lower()
            self.drag_data["piece"] = piece_symbol
            self.drag_data["from_square"] = None
            self.drag_data["is_white"] = is_white
            
            # Create ghost piece on the board canvas
            symbol = self.PIECES[piece_symbol]
            # White = light, Black = dark
            color = '#f5f5f5' if is_white else '#1a1a2e'
            
            # Get position relative to board canvas
            board_x = self.board_canvas.winfo_rootx()
            board_y = self.board_canvas.winfo_rooty()
            x = event.x_root - board_x
            y = event.y_root - board_y
            
            # Draw outline for visibility
            outline_color = '#1a1a2e' if is_white else '#f5f5f5'
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                self.board_canvas.create_text(x+dx, y+dy, text=symbol, 
                    font=('Arial', 40), fill=outline_color, tags='ghost_outline')
            
            self.drag_data["item"] = self.board_canvas.create_text(
                x, y, text=symbol, font=('Arial', 40), fill=color, tags='ghost'
            )
            self._show_status(f"Drag to place {'white' if is_white else 'black'} {piece_type}")
    
    def _sidebar_drag(self, event):
        """Handle dragging from sidebar."""
        if self.drag_data["piece"]:
            # Get position relative to board canvas
            board_x = self.board_canvas.winfo_rootx()
            board_y = self.board_canvas.winfo_rooty()
            x = event.x_root - board_x
            y = event.y_root - board_y
            
            symbol = self.PIECES[self.drag_data["piece"]]
            is_white = self.drag_data.get("is_white", self.drag_data["piece"].isupper())
            
            # Colors: white = light piece with dark outline, black = dark piece with light outline
            piece_color = '#f5f5f5' if is_white else '#1a1a2e'
            outline_color = '#1a1a2e' if is_white else '#f5f5f5'
            
            # Delete old ghost items
            self.board_canvas.delete('ghost')
            self.board_canvas.delete('ghost_outline')
            
            # Draw outline for visibility
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                self.board_canvas.create_text(x+dx, y+dy, text=symbol,
                    font=('Arial', 40), fill=outline_color, tags='ghost_outline')
            
            # Draw ghost piece
            self.drag_data["item"] = self.board_canvas.create_text(
                x, y, text=symbol, font=('Arial', 40), fill=piece_color, tags='ghost'
            )
    
    def _on_click(self, event):
        """Handle click on board."""
        square = self._coords_to_square(event.x, event.y)
        if square is None:
            return
        
        piece = self.board.piece_at(square)
        if piece:
            # Start dragging this piece
            self.drag_data["piece"] = piece.symbol()
            self.drag_data["from_square"] = square
            self.drag_data["is_white"] = piece.color
            
            # Redraw board first (this will hide the piece being dragged)
            self._draw_board()
            
            # Now create ghost on top
            symbol = self.PIECES[piece.symbol()]
            # White pieces = light, Black pieces = dark
            color = '#f5f5f5' if piece.color else '#1a1a2e'
            outline_color = '#1a1a2e' if piece.color else '#f5f5f5'
            
            # Draw outline for visibility
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                self.board_canvas.create_text(event.x+dx, event.y+dy, text=symbol,
                    font=('Arial', 40), fill=outline_color, tags='ghost_outline')
            
            self.drag_data["item"] = self.board_canvas.create_text(
                event.x, event.y, text=symbol, font=('Arial', 40), fill=color, tags='ghost'
            )
    
    def _on_drag(self, event):
        """Handle drag motion on board."""
        if self.drag_data["piece"]:
            symbol = self.PIECES[self.drag_data["piece"]]
            is_white = self.drag_data.get("is_white", self.drag_data["piece"].isupper())
            
            # Colors: white = light piece with dark outline, black = dark piece with light outline
            piece_color = '#f5f5f5' if is_white else '#1a1a2e'
            outline_color = '#1a1a2e' if is_white else '#f5f5f5'
            
            # Delete old ghost items
            self.board_canvas.delete('ghost')
            self.board_canvas.delete('ghost_outline')
            
            # Draw outline for visibility
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                self.board_canvas.create_text(event.x+dx, event.y+dy, text=symbol,
                    font=('Arial', 40), fill=outline_color, tags='ghost_outline')
            
            # Draw ghost piece
            self.drag_data["item"] = self.board_canvas.create_text(
                event.x, event.y, text=symbol, font=('Arial', 40), fill=piece_color, tags='ghost'
            )
    
    def _on_release(self, event):
        """Handle mouse release."""
        if not self.drag_data["piece"]:
            return
        
        # Delete ghost and outline
        self.board_canvas.delete('ghost')
        self.board_canvas.delete('ghost_outline')
        
        # Get coordinates relative to board canvas
        board_x = self.board_canvas.winfo_rootx()
        board_y = self.board_canvas.winfo_rooty()
        rel_x = event.x_root - board_x
        rel_y = event.y_root - board_y
        
        # Check if release is on the board
        if 0 <= rel_x <= self.BOARD_SIZE and 0 <= rel_y <= self.BOARD_SIZE:
            target_square = self._coords_to_square(rel_x, rel_y)
        else:
            target_square = None
        
        if target_square is not None:
            from_sq = self.drag_data["from_square"]
            piece_sym = self.drag_data["piece"]
            
            if from_sq is not None:
                # Moving piece on board
                if target_square != from_sq:
                    move = Move(from_sq, target_square)
                    if move in self.board.legal_moves:
                        self._make_move(move)
                    else:
                        # Just place the piece (for setup mode)
                        self._set_piece(target_square, piece_sym)
                        self._clear_piece(from_sq)
            else:
                # Placing from sidebar
                self._set_piece(target_square, piece_sym)
        elif self.drag_data["from_square"] is not None:
            # Dragged off board - remove piece
            self._clear_piece(self.drag_data["from_square"])
        
        # Reset drag state
        self.drag_data = {"piece": None, "from_square": None, "item": None, "is_white": None}
        self._draw_board()
    
    def _on_right_click(self, event):
        """Handle right click to remove piece."""
        square = self._coords_to_square(event.x, event.y)
        if square is not None:
            self._clear_piece(square)
            self._draw_board()
    
    def _set_piece(self, square, piece_symbol):
        """Set a piece on the board."""
        self.board.set_piece_at(square, Piece.from_symbol(piece_symbol))
        self._draw_board()
    
    def _clear_piece(self, square):
        """Remove a piece from the board."""
        self.board.remove_piece_at(square)
        self._draw_board()
    
    def _execute_move(self):
        """Execute move from the entry field."""
        notation = self.move_entry.get().strip()
        if not notation:
            return
        
        try:
            parser = DescriptiveNotationParser(self.board)
            move = parser.parse(notation)
            
            if move and move in self.board.legal_moves:
                self._make_move(move, notation)
                self.move_entry.delete(0, tk.END)
                self._show_status(f"Played: {notation}")
            else:
                self._show_status(f"Invalid move: {notation}", error=True)
        except Exception as e:
            self._show_status(f"Error: {str(e)}", error=True)
    
    def _make_move(self, move, notation=None, animate=True):
        """Make a move on the board."""
        # If we're not at the end, truncate future moves
        if self.current_move_index < len(self.board_states) - 1:
            self.board_states = self.board_states[:self.current_move_index + 1]
            self.move_history = self.move_history[:self.current_move_index]
            self.move_notations = self.move_notations[:self.current_move_index]
            self._rebuild_history_display()
        
        self.move_history.append(self.board.fen())
        
        # Generate descriptive notation before pushing
        if notation is None:
            notation = MoveToDescriptive.convert(self.board, move)
        
        self.move_notations.append(notation)
        
        from_sq = move.from_square
        to_sq = move.to_square
        piece = self.board.piece_at(from_sq)
        
        self.board.push(move)
        
        # Store the new board state
        self.board_states.append(self.board.fen())
        self.current_move_index = len(self.board_states) - 1
        
        # Animate or just draw
        if animate and piece:
            self._animate_piece_move_forward(from_sq, to_sq, piece)
        else:
            self._draw_board()
        
        self._update_turn()
        self._add_history(notation)
        self._update_nav_label()
        self._highlight_current_move()
        self._check_game_state()
    
    def _animate_piece_move_forward(self, from_sq, to_sq, piece):
        """Animate a piece moving forward (for making moves)."""
        self.animating = True
        
        # Get coordinates
        start_x, start_y = self._square_to_coords(from_sq)
        end_x, end_y = self._square_to_coords(to_sq)
        
        # Calculate step sizes
        dx = (end_x - start_x) / self.animation_steps
        dy = (end_y - start_y) / self.animation_steps
        step_delay = self.animation_duration // self.animation_steps
        
        # Draw board without the moving piece at its origin
        temp_board = Board(self.move_history[-1])  # Board before the move
        temp_board.remove_piece_at(from_sq)
        old_board = self.board
        self.board = temp_board
        self._draw_board()
        self.board = old_board
        
        # Create the animated piece
        symbol = self.PIECES[piece.symbol()]
        color = '#f5f5f5' if piece.color else '#1a1a2e'
        outline_color = '#1a1a2e' if piece.color else '#f5f5f5'
        
        def animate_step(step, x, y):
            if step > self.animation_steps:
                # Animation complete
                self._draw_board()
                self.animating = False
                return
            
            # Clear previous animated piece
            self.board_canvas.delete('animated')
            
            # Draw piece at current position with outline
            for ddx, ddy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                self.board_canvas.create_text(x+ddx, y+ddy, text=symbol,
                    font=('Arial', 40), fill=outline_color, tags='animated')
            self.board_canvas.create_text(x, y, text=symbol,
                font=('Arial', 40), fill=color, tags='animated')
            
            # Schedule next step
            self.root.after(step_delay, lambda: animate_step(step + 1, x + dx, y + dy))
        
        # Start animation
        animate_step(0, start_x, start_y)
    
    def _rebuild_history_display(self):
        """Rebuild the history display from move_notations."""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        for i, notation in enumerate(self.move_notations):
            num = i + 1
            who = "W" if num % 2 == 1 else "B"
            self.history_text.insert(tk.END, f"{num}. {who}: {notation}\n")
        self.history_text.config(state=tk.DISABLED)
    
    def _update_turn(self):
        """Update turn indicator."""
        text = "White to move" if self.board.turn else "Black to move"
        self.turn_label.config(text=text)
    
    def _add_history(self, notation):
        """Add move to history in descriptive notation."""
        self.history_text.config(state=tk.NORMAL)
        num = len(self.move_history)
        who = "W" if num % 2 == 1 else "B"
        self.history_text.insert(tk.END, f"{num}. {who}: {notation}\n")
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
    
    def _check_game_state(self):
        """Check for checkmate, stalemate, etc."""
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn else "White"
            self._show_status(f"Checkmate! {winner} wins!")
        elif self.board.is_stalemate():
            self._show_status("Stalemate!")
        elif self.board.is_check():
            self._show_status("Check!")
    
    def _show_status(self, msg, error=False):
        """Show status message."""
        color = '#ff6b6b' if error else '#888'
        self.status_label.config(text=msg, foreground=color)
    
    def _reset_board(self):
        """Reset to starting position."""
        self.board = Board()
        self.move_history = []
        self.move_notations = []
        self.board_states = [Board().fen()]
        self.current_move_index = 0
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        self.history_text.config(state=tk.DISABLED)
        self._draw_board()
        self._update_turn()
        self._update_nav_label()
        self._show_status("Board reset")
    
    def _clear_board(self):
        """Clear the board completely."""
        self.board.clear()
        self.move_history = []
        self.move_notations = []
        self.board_states = [self.board.fen()]
        self.current_move_index = 0
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        self.history_text.config(state=tk.DISABLED)
        self._draw_board()
        self._update_nav_label()
        self._show_status("Board cleared")
    
    def _undo_move(self):
        """Undo last move (removes it from history)."""
        if len(self.board_states) > 1:
            # Remove the last state
            self.board_states.pop()
            if self.move_history:
                self.move_history.pop()
            if self.move_notations:
                self.move_notations.pop()
            
            # Go to the new end
            self.current_move_index = len(self.board_states) - 1
            self.board = Board(self.board_states[self.current_move_index])
            
            self._draw_board()
            self._update_turn()
            self._rebuild_history_display()
            self._update_nav_label()
            self._highlight_current_move()
            
            self._show_status("Move undone")
        else:
            self._show_status("Nothing to undo", error=True)
    
    def _switch_turn(self):
        """Switch whose turn it is (white/black)."""
        # Get current FEN and modify the turn
        fen_parts = self.board.fen().split(' ')
        # Toggle turn: 'w' -> 'b', 'b' -> 'w'
        fen_parts[1] = 'b' if fen_parts[1] == 'w' else 'w'
        new_fen = ' '.join(fen_parts)
        
        self.board = Board(new_fen)
        self._update_turn()
        self._draw_board()
        turn_name = "White" if self.board.turn else "Black"
        self._show_status(f"Switched to {turn_name}'s turn")
    
    def _go_to_start(self):
        """Go to the starting position."""
        if self.current_move_index > 0:
            self._navigate_to_move(0)
    
    def _go_back(self):
        """Go back one move."""
        if self.current_move_index > 0:
            self._navigate_to_move(self.current_move_index - 1)
    
    def _go_forward(self):
        """Go forward one move."""
        if self.current_move_index < len(self.board_states) - 1:
            self._navigate_to_move(self.current_move_index + 1)
    
    def _go_to_end(self):
        """Go to the latest position."""
        if self.current_move_index < len(self.board_states) - 1:
            self._navigate_to_move(len(self.board_states) - 1)
    
    def _navigate_to_move(self, index, animate=True):
        """Navigate to a specific move index."""
        if self.animating:
            return
        
        old_index = self.current_move_index
        self.current_move_index = index
        
        # Get the board state at this index
        target_fen = self.board_states[index]
        
        if animate and abs(index - old_index) == 1:
            # Single move - animate it
            self._animate_navigation(old_index, index)
        else:
            # Multiple moves or no animation - just set the position
            self.board = Board(target_fen)
            self._draw_board()
        
        self._update_turn()
        self._update_nav_label()
        self._highlight_current_move()
    
    def _animate_navigation(self, from_index, to_index):
        """Animate navigation between adjacent moves."""
        if from_index < to_index:
            # Going forward - animate the move that was made
            old_board = Board(self.board_states[from_index])
            new_board = Board(self.board_states[to_index])
        else:
            # Going backward - animate the reverse of the move
            old_board = Board(self.board_states[from_index])
            new_board = Board(self.board_states[to_index])
        
        # Find what changed between boards
        from_square = None
        to_square = None
        moving_piece = None
        
        for sq in SQUARES:
            old_piece = old_board.piece_at(sq)
            new_piece = new_board.piece_at(sq)
            
            if old_piece and not new_piece:
                if from_square is None:
                    from_square = sq
                    moving_piece = old_piece
            elif new_piece and not old_piece:
                to_square = sq
                if moving_piece is None:
                    moving_piece = new_piece
            elif old_piece and new_piece and old_piece.symbol() != new_piece.symbol():
                # Piece changed (capture or replacement)
                if from_square is None:
                    from_square = sq
                    moving_piece = old_piece
                to_square = sq
        
        if from_square is not None and to_square is not None and moving_piece:
            self._animate_piece_move(from_square, to_square, moving_piece, new_board)
        else:
            # Can't determine animation, just update
            self.board = new_board
            self._draw_board()
    
    def _animate_piece_move(self, from_sq, to_sq, piece, final_board):
        """Animate a piece moving from one square to another."""
        self.animating = True
        
        # Get coordinates
        start_x, start_y = self._square_to_coords(from_sq)
        end_x, end_y = self._square_to_coords(to_sq)
        
        # Calculate step sizes
        dx = (end_x - start_x) / self.animation_steps
        dy = (end_y - start_y) / self.animation_steps
        step_delay = self.animation_duration // self.animation_steps
        
        # Draw board without the moving piece
        temp_board = Board(self.board.fen())
        temp_board.remove_piece_at(from_sq)
        self.board = temp_board
        self._draw_board()
        
        # Create the animated piece
        symbol = self.PIECES[piece.symbol()]
        color = '#f5f5f5' if piece.color else '#1a1a2e'
        outline_color = '#1a1a2e' if piece.color else '#f5f5f5'
        
        def animate_step(step, x, y):
            if step > self.animation_steps:
                # Animation complete
                self.board = final_board
                self._draw_board()
                self.animating = False
                return
            
            # Clear previous animated piece
            self.board_canvas.delete('animated')
            
            # Draw piece at current position with outline
            for ddx, ddy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                self.board_canvas.create_text(x+ddx, y+ddy, text=symbol,
                    font=('Arial', 40), fill=outline_color, tags='animated')
            self.board_canvas.create_text(x, y, text=symbol,
                font=('Arial', 40), fill=color, tags='animated')
            
            # Schedule next step
            self.root.after(step_delay, lambda: animate_step(step + 1, x + dx, y + dy))
        
        # Start animation
        animate_step(0, start_x, start_y)
    
    def _update_nav_label(self):
        """Update the navigation position label."""
        if self.current_move_index == 0:
            self.move_label.config(text="Start")
        else:
            total = len(self.board_states) - 1
            self.move_label.config(text=f"{self.current_move_index}/{total}")
    
    def _highlight_current_move(self):
        """Highlight the current move in the history."""
        self.history_text.config(state=tk.NORMAL)
        
        # Remove all existing highlights
        self.history_text.tag_remove('highlight', '1.0', tk.END)
        
        # If we're not at the start, highlight the current move's line
        if self.current_move_index > 0:
            line_num = self.current_move_index
            start_idx = f"{line_num}.0"
            end_idx = f"{line_num}.end"
            self.history_text.tag_add('highlight', start_idx, end_idx)
            
            # Make sure the highlighted line is visible
            self.history_text.see(start_idx)
        
        self.history_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = ChessBoardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
