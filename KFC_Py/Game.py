import queue, threading, time, math, logging
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import cv2
from Board import Board
from Command import Command
from Piece import Piece
import numpy as np
import pathlib
from BackgroundBoardFactory import create_background_board
from PubSub import pubsub

from scoreBoard import ScoreBoard
from MoveLog import MoveLog
from SoundManager import SoundManager
from img import Img
from Announcer import Announcer

from KeyboardInput import KeyboardProcessor, KeyboardProducer

# set up a module-level logger – real apps can configure handlers/levels
logger = logging.getLogger(__name__)


class InvalidBoard(Exception): ...


class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        self.pieces = pieces
        self.board = board
        self.curr_board = None
        self.user_input_queue = queue.Queue()
        self.piece_by_id = {p.id: p for p in pieces}
        self.pos: Dict[Tuple[int, int], List[Piece]] = defaultdict(list)
        self.START_NS = time.time_ns()
        self._time_factor = 1  
        self.kp1 = None
        self.kp2 = None
        self.kb_prod_1 = None
        self.kb_prod_2 = None
        self.selected_id_1: Optional[str] = None
        self.selected_id_2: Optional[str] = None  
        self.last_cursor1 = (0, 0)
        self.last_cursor2 = (0, 0)
        self.opening_message_duration = 3  # שניות
        self.closing_message_duration = 3  # שניות

        #board = create_background_board("../pieces/background.png", "../pieces/board.png")
        self.scoreboard = ScoreBoard()
        self.move_log = MoveLog()
        self.sound = SoundManager(pubsub)
        self.announcer = Announcer()
        self.register_event_listeners()


    def register_event_listeners(self):
        pubsub.subscribe("capture", self.scoreboard.handle_capture)
        pubsub.subscribe("move", self.move_log.handle_move)
        pubsub.subscribe("game_start", self.announcer.show_start)
        pubsub.subscribe("game_over", self.announcer.show_end)
    def game_time_ms(self) -> int:
        return self._time_factor * (time.monotonic_ns() - self.START_NS) // 1_000_000

    def clone_board(self) -> Board:
        return self.board.clone()

    def start_user_input_thread(self):

        # player 1 key‐map
        p1_map = {
            "up": "up", "down": "down", "left": "left", "right": "right",
            "enter": "select", "space": "select", "+": "jump"
        }
        # player 2 key‐map
        p2_map = {
            "w": "up", "s": "down", "a": "left", "d": "right",
            "f": "select", "space": "select", "g": "jump"
        }

        # create two processors with initial positions
        # Player 1 (white) starts at bottom (row 7), Player 2 (black) starts at top (row 0)
        self.kp1 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p1_map,
                                     initial_pos=(7, 0))  # White pieces start at bottom
        self.kp2 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p2_map,
                                     initial_pos=(0, 0))  # Black pieces start at top

        # **pass the player number** as the 4th argument!
        self.kb_prod_1 = KeyboardProducer(self,
                                          self.user_input_queue,
                                          self.kp1,
                                          player=1)
        self.kb_prod_2 = KeyboardProducer(self,
                                          self.user_input_queue,
                                          self.kp2,
                                          player=2)

        self.kb_prod_1.start()
        self.kb_prod_2.start()

    def _update_cell2piece_map(self):
        self.pos.clear()
        for p in self.pieces:
            self.pos[p.current_cell()].append(p)

    def _run_game_loop(self, num_iterations=None, is_with_graphics=True):
        it_counter = 0
        while not self._is_win():
            now = self.game_time_ms()

            for p in self.pieces:
                p.update(now)

            self._update_cell2piece_map()

            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)

            if is_with_graphics:
                self._draw()
                self._show()

            self._resolve_collisions()

            # for testing
            if num_iterations is not None:
                it_counter += 1
                if num_iterations <= it_counter:
                    return

    def run(self, num_iterations=None, is_with_graphics=True):
       
        self.start_user_input_thread()
        start_ms = self.START_NS
        for p in self.pieces:
            p.reset(start_ms)
        pubsub.publish("game_start", {})
        self._run_game_loop(num_iterations, is_with_graphics)
        pubsub.publish("game_end", {"winner": self._side_of(self.pieces[0].id)})  # Assume first piece's side is the winner     
        self._announce_win()
        if self.kb_prod_1:
            self.kb_prod_1.stop()
            self.kb_prod_2.stop()


    def draw(self, frame):
        # ציור כל הכלים על הלוח
        for piece in self.pieces:
            if piece.alive:
                x = 384 + piece.col * 64
                y = 104 + piece.row * 64
                resized_img = cv2.resize(piece.image, (64, 64))
                frame[y:y+64, x:x+64] = resized_img

        # ציור תור נוכחי (לבן או שחור)
        turn_text = f"{self.current_turn.capitalize()}'s Turn"
        cv2.putText(frame, turn_text, (600, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # ציור ניקוד
        white_score = self.score.get("white", 0)
        black_score = self.score.get("black", 0)
        cv2.putText(frame, f"White: {white_score}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, f"Black: {black_score}", (30, 670),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # ציור מהלך אחרון (אם קיים)
        if hasattr(self, 'last_move') and self.last_move:
            cv2.putText(frame, f"Last: {self.last_move}", (1000, 300),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        # ציור רשימת מהלכים אחרונים (אם קיימת)
        if hasattr(self, 'move_log'):
            for i, move in enumerate(self.move_log[-10:]):
                y = 350 + i * 25
                cv2.putText(frame, move, (1000, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        # ציור כיתוב סיום (אם רלוונטי)
        if getattr(self, 'game_over', False):
            winner = self.winner if hasattr(self, 'winner') else "Unknown"
            msg = f"{winner.capitalize()} Wins!"
            cv2.putText(frame, msg, (400, 360),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

    def _draw(self):
        self.curr_board = self.clone_board()
        for p in self.pieces:
            p.draw_on_board(self.curr_board, now_ms=self.game_time_ms())

        # overlay both players' cursors, but only log on change
        if self.kp1 and self.kp2:
            for player, kp, last in (
                    (1, self.kp1, 'last_cursor1'),
                    (2, self.kp2, 'last_cursor2')
            ):
                r, c = kp.get_cursor()
                # draw rectangle
                y1 = r * self.board.cell_H_pix + self.board.offset_y
                x1 = c * self.board.cell_W_pix + self.board.offset_x
                y2 = y1 + self.board.cell_H_pix - 1
                x2 = x1 + self.board.cell_W_pix - 1
                color = (0, 255, 0) if player == 1 else (255, 0, 0)
                self.curr_board.img.draw_rect(x1, y1, x2, y2, color)

                # only print if moved
                prev = getattr(self, last)
                if prev != (r, c):
                    logger.debug("Marker P%s moved to (%s, %s)", player, r, c)
                    setattr(self, last, (r, c))

    def _show(self):
        self.announcer.overlay_message(self.curr_board.img.img)

        self.curr_board.show()

    def _side_of(self, piece_id: str) -> str:
        return piece_id[1]

    def _process_input(self, cmd: Command):
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            logger.debug("Unknown piece id %s", cmd.piece_id)
            return

        # Process the command - Piece.on_command() determines my_color internally
        mover.on_command(cmd, self.pos)
        
        pubsub.publish("move", {"piece_id": cmd.piece_id, "cmd": cmd})

        logger.info(f"Processed command: {cmd} for piece {cmd.piece_id}")

    def _resolve_collisions(self):
        self._update_cell2piece_map()
        occupied = self.pos

        for cell, plist in occupied.items():
            if len(plist) < 2:
                continue

            logger.debug(f"Collision detected at {cell}: {[p.id for p in plist]}")

            # Choose the piece that most recently entered the square
            # But prioritize pieces that are actually moving over idle pieces
            moving_pieces = [p for p in plist if p.state.name != 'idle']
            if moving_pieces:

                winner = max(moving_pieces, key=lambda p: p.state.physics.get_start_ms())
                logger.debug(f"Winner (moving): {winner.id} (state: {winner.state.name})")
            else:
                # If no moving pieces, choose the most recent idle piece
                winner = max(plist, key=lambda p: p.state.physics.get_start_ms())
                logger.debug(f"Winner (idle): {winner.id} (state: {winner.state.name})")

            # Determine if captures allowed: default allow
            if not winner.state.can_capture():
                # Allow capture even for idle pieces to satisfy game rules
                pass

            # Remove every other piece that *can be captured*
            for p in plist:
                if p is winner:
                    continue
                if p.state.can_be_captured():
                    logger.debug(f"Checking if {p.id} can be captured (state: {p.state.name})")
                    
                    # Don't remove knights that are moving (they're jumping in the air)
                    if p.id.startswith(('NW', 'NB')) and p.state.name == 'move':
                        logger.debug(f"Knight {p.id} is moving (jumping) - not removing")
                        continue
                    # Don't remove pieces that are jumping (they're in the air)
                    if p.state.name == 'jump':
                        logger.debug(f"Piece {p.id} is jumping - not removing")
                        continue
                    # Don't remove pieces if the winner is jumping (winner is in the air)
                    if winner.state.name == 'jump':
                        logger.debug(f"Winner {winner.id} is jumping - not removing {p.id}")
                        continue
                    # Don't remove pieces if the winner is a knight moving (knight is jumping in the air)
                    if winner.id.startswith(('NW', 'NB')) and winner.state.name == 'move':
                        logger.debug(f"Winner knight {winner.id} is moving (jumping) - not removing {p.id}")
                        continue
                    
                    # Don't capture pieces of the same color (friendly pieces)
                    if winner.id[1] == p.id[1]:  # Same color (W/B)
                        logger.debug(f"Winner {winner.id} and {p.id} are same color - not capturing")
                        continue
                    
                    logger.info(f"CAPTURE: {winner.id} captures {p.id} at {cell}")
                    pubsub.publish("capture", {
                        "attacker": winner.id,
                        "victim": p.id,
                        "cell": cell
                    })
                    self.pieces.remove(p)
                else:
                    logger.debug(f"Piece {p.id} cannot be captured (state: {p.state.name})")

    def _validate(self, pieces):
        """Ensure both kings present and no two pieces share a cell."""
        has_white_king = has_black_king = False
        seen_cells: dict[tuple[int, int], str] = {}
        for p in pieces:
            cell = p.current_cell()
            if cell in seen_cells:
                # Allow overlap only if piece is from opposite side
                if seen_cells[cell] == p.id[1]:
                    return False
            else:
                seen_cells[cell] = p.id[1]
            if p.id.startswith("KW"):
                has_white_king = True
            elif p.id.startswith("KB"):
                has_black_king = True
        return has_white_king and has_black_king

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces if p.id.startswith(('KW', 'KB'))]
        return len(kings) < 2

    def _announce_win(self):
        winner = 'Black' if any(p.id.startswith('KB') for p in self.pieces) else 'White'
        logger.info(f"{winner} wins!")

        pubsub.publish("game_over", {"winner": winner})
