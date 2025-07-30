import unittest
import time
from unittest.mock import Mock

from Game import Game
from Board import Board
from Piece import Piece
from State import State
from Physics import IdlePhysics, MovePhysics, JumpPhysics
from Graphics import Graphics
from Moves import Moves
from Command import Command
from img import Img


class TestCollisions(unittest.TestCase):
    
    def setUp(self):
        # Create a simple board with mock image
        mock_img = Mock(spec=Img)
        self.board = Board(64, 64, 8, 8, mock_img)
        
        # Create mock graphics
        self.mock_graphics = Mock(spec=Graphics)
        self.mock_graphics.get_img.return_value = Mock()
        
        # Create mock moves
        self.mock_moves = Mock(spec=Moves)
        self.mock_moves.is_valid.return_value = True
        
        # Create pieces for testing
        self.pieces = []
        
    def create_piece(self, piece_id, cell, state_name="idle"):
        """Helper to create a piece with specific state"""
        if state_name == "idle":
            physics = IdlePhysics(self.board)
        elif state_name == "move":
            physics = MovePhysics(self.board, 1.0)
        elif state_name == "jump":
            physics = JumpPhysics(self.board, 1.0)
        else:
            raise ValueError(f"Unknown state: {state_name}")
            
        state = State(self.mock_moves, self.mock_graphics, physics)
        state.name = state_name
        
        piece = Piece(piece_id, state)
        
        # For move/jump states, we need both start and end cells
        if state_name in ["move", "jump"]:
            end_cell = (cell[0] + 1, cell[1] + 1)  # Move diagonally
            piece.state.reset(Command(time.time_ns(), piece_id, "idle", [cell, end_cell]))
        else:
            piece.state.reset(Command(time.time_ns(), piece_id, "idle", [cell]))
            
        return piece
    
    def test_no_collision_when_piece_jumping(self):
        """Test that no collision occurs when one piece is jumping"""
        
        # Create two pieces in the same cell
        piece1 = self.create_piece("PW_1", (1, 1), "idle")  # Standing piece
        piece2 = self.create_piece("PW_2", (1, 1), "jump")  # Jumping piece
        
        # Set different start times so piece2 is "winner"
        piece2.state.physics._start_ms = piece1.state.physics._start_ms + 1000
        
        self.pieces = [piece1, piece2]
        game = Game(self.pieces, self.board, skip_validation=True)
        
        # Store initial piece count
        initial_count = len(game.pieces)
        
        # Run collision resolution
        game._resolve_collisions()
        
        # Both pieces should still exist (no collision)
        self.assertEqual(len(game.pieces), initial_count, 
                        "Pieces should not collide when one is jumping")
    
    def test_no_collision_when_winner_jumping(self):
        """Test that no collision occurs when the winner piece is jumping"""
        
        # Create two pieces in the same cell
        piece1 = self.create_piece("PW_1", (1, 1), "jump")  # Jumping piece (winner)
        piece2 = self.create_piece("PW_2", (1, 1), "idle")  # Standing piece
        
        # Set different start times so piece1 is "winner"
        piece1.state.physics._start_ms = piece2.state.physics._start_ms + 1000
        
        self.pieces = [piece1, piece2]
        game = Game(self.pieces, self.board, skip_validation=True)
        
        # Store initial piece count
        initial_count = len(game.pieces)
        
        # Run collision resolution
        game._resolve_collisions()
        
        # Both pieces should still exist (no collision)
        self.assertEqual(len(game.pieces), initial_count, 
                        "Pieces should not collide when winner is jumping")
    
    def test_collision_when_both_idle(self):
        """Test that collision occurs when both pieces are idle and from different colors"""
        
        # Create two pieces in the same cell from different colors
        piece1 = self.create_piece("PW_1", (1, 1), "idle")  # White piece
        piece2 = self.create_piece("PB_2", (1, 1), "idle")  # Black piece
        
        # Set different start times so piece2 is "winner"
        piece2.state.physics._start_ms = piece1.state.physics._start_ms + 1000
        
        self.pieces = [piece1, piece2]
        game = Game(self.pieces, self.board, skip_validation=True)
        
        # Run collision resolution
        game._resolve_collisions()
        
        # Only winner should remain
        self.assertEqual(len(game.pieces), 1, 
                        "Collision should occur when both pieces are idle")
        self.assertEqual(game.pieces[0].id, "PB_2", 
                        "Winner should remain")
    
    def test_same_color_no_collision(self):
        """Test that pieces of the same color don't capture each other"""
        
        # Create two pieces of the same color in the same cell
        piece1 = self.create_piece("PW_1", (1, 1), "idle")  # White piece
        piece2 = self.create_piece("PW_2", (1, 1), "idle")  # White piece
        
        # Set different start times so piece2 would be "winner"
        piece2.state.physics._start_ms = piece1.state.physics._start_ms + 1000
        
        self.pieces = [piece1, piece2]
        game = Game(self.pieces, self.board, skip_validation=True)
        
        # Run collision resolution
        game._resolve_collisions()
        
        # Both pieces should remain (no capture between same color)
        self.assertEqual(len(game.pieces), 2, 
                        "Same color pieces should not capture each other")
        self.assertIn(piece1, game.pieces, "First piece should remain")
        self.assertIn(piece2, game.pieces, "Second piece should remain")
    
    def test_knight_moving_no_collision(self):
        """Test that knights moving don't cause collisions"""
        
        # Create knight and another piece in the same cell
        knight = self.create_piece("NW_1", (1, 1), "move")  # Knight moving
        piece2 = self.create_piece("PW_1", (1, 1), "idle")  # Standing piece
        
        # Set different start times so knight is "winner"
        knight.state.physics._start_ms = piece2.state.physics._start_ms + 1000
        
        self.pieces = [knight, piece2]
        game = Game(self.pieces, self.board, skip_validation=True)
        
        # Store initial piece count
        initial_count = len(game.pieces)
        
        # Run collision resolution
        game._resolve_collisions()
        
        # Both pieces should still exist (no collision)
        self.assertEqual(len(game.pieces), initial_count, 
                        "Knight moving should not cause collision")
    
    def test_debug_knight_moving_collision(self):
        """Debug test to see what's happening with knight collision"""
        
        # Create knight and another piece in the same cell
        knight = self.create_piece("NW_1", (1, 1), "move")  # Knight moving
        piece2 = self.create_piece("PW_1", (1, 1), "idle")  # Standing piece
        
        # Set different start times so knight is "winner"
        knight.state.physics._start_ms = piece2.state.physics._start_ms + 1000
        
        self.pieces = [knight, piece2]
        game = Game(self.pieces, self.board, skip_validation=True)
        
        # Debug: Print piece states before collision resolution
        print(f"\nBefore collision resolution:")
        for piece in game.pieces:
            print(f"  {piece.id}: state={piece.state.name}, can_be_captured={piece.state.can_be_captured()}")
        
        # Run collision resolution
        game._resolve_collisions()
        
        # Debug: Print piece states after collision resolution
        print(f"\nAfter collision resolution:")
        for piece in game.pieces:
            print(f"  {piece.id}: state={piece.state.name}")
        
        # Both pieces should still exist (no collision)
        self.assertEqual(len(game.pieces), 2, 
                        "Knight moving should not cause collision")


if __name__ == '__main__':
    unittest.main()
