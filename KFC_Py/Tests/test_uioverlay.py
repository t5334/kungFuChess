import numpy as np
from UIOverlay import UIOverlay
from MoveLogger import MoveLogger
from ScoreBoard import Scoreboard

def test_draw_overlay_runs():
    logger = MoveLogger()
    scoreboard = Scoreboard()
    overlay = UIOverlay(logger, scoreboard)
    frame = np.zeros((600, 800, 3), dtype=np.uint8)
    logger.log_move("black", "Pawn2", "e7", "e5")
    output = overlay.draw_overlay(frame)
    assert output.shape == frame.shape
