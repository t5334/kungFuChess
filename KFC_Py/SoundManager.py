# SoundManager.py
import pygame
import pathlib
import logging

logger = logging.getLogger(__name__)

class SoundManager:
    def __init__(self, pubsub):
        pygame.mixer.init()
        base = pathlib.Path(__file__).parent.parent / "pieces"
        self.sounds = {
            "move": pygame.mixer.Sound(str(base / "move.wav")),
            "capture": pygame.mixer.Sound(str(base / "capture.wav")),
        }
        pubsub.subscribe("move", self.play_move)
        pubsub.subscribe("capture", self.play_capture)

    def play_move(self, event_data=None):
        logger.debug("[Sound] Playing move.wav")
        self.sounds["move"].play()

    def play_capture(self, event_data=None):
        logger.debug("[SOUND] Playing capture sound")
        self.sounds["capture"].play()
