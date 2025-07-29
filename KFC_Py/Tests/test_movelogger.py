import pytest
from MoveLogger import MoveLogger

def test_log_move_without_capture():
    logger = MoveLogger()
    logger.log_move("white", "P", "e2", "e4")
    assert logger.get_moves("white") == ["P: e2→e4"]
    assert logger.get_points("white") == 0

def test_log_move_with_capture():
    logger = MoveLogger()
    logger.log_move("black", "N", "g8", "f6", ate=True)
    assert logger.get_moves("black") == ["N: g8→f6 ×"]
    assert logger.get_points("black") == 1

def test_multiple_moves():
    logger = MoveLogger()
    logger.log_move("white", "B", "c1", "g5")
    logger.log_move("white", "Q", "d1", "h5", ate=True)
    logger.log_move("black", "P", "e7", "e5")
    logger.log_move("black", "K", "e8", "e7")
    assert logger.get_moves("white") == ["B: c1→g5", "Q: d1→h5 ×"]
    assert logger.get_moves("black") == ["P: e7→e5", "K: e8→e7"]
    assert logger.get_points("white") == 1
    assert logger.get_points("black") == 0

def test_reset_logger():
    logger = MoveLogger()
    logger.log_move("white", "R", "a1", "a8", ate=True)
    logger.reset()
    assert logger.get_moves("white") == []
    assert logger.get_points("white") == 0
