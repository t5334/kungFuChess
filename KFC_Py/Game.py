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
from MoveLogger import MoveLogger
from UIOverlay import UIOverlay
from SoundManager import SoundManager
from img import Img


class InvalidBoard(Exception):
    """Raised when board setup is invalid"""
    pass
from ScoreBoard import Scoreboard
from Announcer import Announcer
from KeyboardInput import KeyboardProcessor, KeyboardProducer


# set up a module-level logger – real apps can configure handlers/levels
logger = logging.getLogger(__name__)


class InvalidBoard(Exception): ...


class Game:
    def __init__(self, pieces: List[Piece], board: Board, skip_validation: bool = False):
        self.pieces = pieces
        self.board = board
        
        # Validate the board after basic initialization (unless skipped for tests)
        if not skip_validation:
            self._validate(pieces)
            
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
        self.logger = MoveLogger()
        self.score = Scoreboard()
        self.overlay = UIOverlay(self.logger, self.score)
        #board = create_background_board("../pieces/background.png", "../pieces/board.png")
        self.sound = SoundManager(pubsub)
        self.announcer = Announcer()
        self.register_event_listeners()


    def register_event_listeners(self):
        pubsub.subscribe("capture", self.score.handle_capture)
        pubsub.subscribe("move", self.logger.handle_move)
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
            "enter": "select", "+": "jump"#, "space": "select",
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
        game_ended = False
        victory_screen_shown = False
        
        while not game_ended:
            now = self.game_time_ms()

            # אם המשחק עדיין פעיל
            if not victory_screen_shown and not self._is_win():
                for p in self.pieces:
                    p.update(now)

                self._update_cell2piece_map()

                while not self.user_input_queue.empty():
                    cmd: Command = self.user_input_queue.get()
                    self._process_input(cmd)

                self._resolve_collisions()
                
                # בדיקה אם המשחק הסתיים
                if self._is_win():
                    victory_screen_shown = True
                    # פרסום אירוע סיום המשחק
                    winner = 'Black' if any(p.id.startswith('KB') for p in self.pieces) else 'White'
                    pubsub.publish("game_over", {"winner": winner})

            if is_with_graphics:
                self._draw()
                should_exit = self._show()
                # רק אם תמונת הסיום הסתיימה, נסגור את המשחק
                if should_exit and victory_screen_shown:
                    game_ended = True

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
        
        # הודעה על סיום במסוף
        winner = 'Black' if any(p.id.startswith('KB') for p in self.pieces) else 'White'
        logger.info(f"{winner} wins!")
        
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
        if hasattr(self, 'logger'):
            for i, move in enumerate(self.logger[-10:]):
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

        # הצגת מסגרת סביב הכלי הנבחר
        for player, selected_id in ((1, self.selected_id_1), (2, self.selected_id_2)):
            if selected_id:
                # מצא את הכלי הנבחר
                selected_piece = self.piece_by_id.get(selected_id)
                if selected_piece:
                    # בדוק שהכלי שייך לשחקן הנכון
                    piece_color = selected_piece.id[1]  # W או B
                    expected_color = 'W' if player == 1 else 'B'  # שחקן 1 = לבן, שחקן 2 = שחור
                    
                    if piece_color == expected_color:
                        # קבל את המיקום הנוכחי של הכלי
                        r, c = selected_piece.current_cell()
                        
                        # צייר מסגרת עבה סביב הכלי הנבחר
                        y1 = r * self.board.cell_H_pix + self.board.offset_y
                        x1 = c * self.board.cell_W_pix + self.board.offset_x
                        y2 = y1 + self.board.cell_H_pix - 1
                        x2 = x1 + self.board.cell_W_pix - 1
                        
                        # צבע שונה לכל שחקן - כתום לשחקן 1, ורוד לשחקן 2
                        color = (0, 165, 255) if player == 1 else (255, 0, 255)  # כתום או ורוד
                        thickness = 4  # עובי המסגרת
                        
                        # צייר מסגרת עבה
                        for i in range(thickness):
                            self.curr_board.img.draw_rect(x1-i, y1-i, x2+i, y2+i, color)

    def _show(self):
        self.announcer.overlay_message(self.curr_board.img.img)
        frame = self.curr_board.img.img
        frame = self.overlay.draw_overlay(frame)  # ← כאן
        self.curr_board.show()
        
        # בדיקה אם תמונת הסיום הסתיימה (אחרי 5 שניות)
        if self.announcer.is_victory_screen_finished():
            return True  # סיגנל ליציאה מהמשחק

    def _side_of(self, piece_id: str) -> str:
        return piece_id[1]

    def _process_input(self, cmd: Command):
        color_char = cmd.piece_id[1].upper()
        color = "white" if color_char == "W" else "black"
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            logger.debug("Unknown piece id %s", cmd.piece_id)
            return

        # שמור את המצב הקודם כדי לבדוק אם המהלך בוצע בהצלחה
        old_state = mover.state
        
        # Process the command - Piece.on_command() determines my_color internally
        mover.on_command(cmd, self.pos)
        
        # בדוק אם המצב השתנה (המהלך בוצע בהצלחה)
        if mover.state == old_state:
            logger.debug(f"Command {cmd.type} failed for piece {cmd.piece_id} - state unchanged")
            return  # לא מפרסמים הודעה על מהלך כושל
        
        # Handle different command types based on number of parameters
        if len(cmd.params) >= 2:
            # Commands with two or more parameters (from, to)
            from_cell, to_cell = cmd.params[:2]
            ate = cmd.params[2] if len(cmd.params) > 2 else False
        else:
            # Commands with one parameter or no parameters
            from_cell = cmd.params[0] if cmd.params else None
            to_cell = None
            ate = False

        pubsub.publish("move", {
            "piece": cmd.piece_id[0],
            "color": color,
            "from": from_cell,
            "to": to_cell,
            "ate": ate
        })
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
                        "attacker_color": winner.id[1],
                        "piece_type": p.id[0].upper(),
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
                # Same color pieces cannot overlap
                if seen_cells[cell] == p.id[1]:
                    raise InvalidBoard("Same color pieces cannot overlap")
                # Different colors can overlap (for captures)
            seen_cells[cell] = p.id[1]
            if p.id.startswith("KW"):
                has_white_king = True
            elif p.id.startswith("KB"):
                has_black_king = True
        
        if not has_white_king:
            raise InvalidBoard("Missing white king")
        if not has_black_king:
            raise InvalidBoard("Missing black king")
        
        return True

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces if p.id.startswith(('KW', 'KB'))]
        return len(kings) < 2

    def _announce_win(self):
        winner = 'Black' if any(p.id.startswith('KB') for p in self.pieces) else 'White'
        logger.info(f"{winner} wins!")
        pubsub.publish("game_over", {"winner": winner})
        
