# Announcer.py
import time
import cv2
from PubSub import pubsub 


class Announcer:
    def __init__(self):
        self.message = None
        self.start_time = None
        self.duration = 3  # seconds
        pubsub.subscribe("game_start", self.show_start)
        pubsub.subscribe("game_over", self.show_end)

    def show_start(self, data):
        self.message = "Strategy. Speed. Victory. The game has started!"


        self.start_time = time.time()

    def show_end(self, data):
        winner = data.get("winner", "לא ידוע")
        self.message = f"Well played! {winner} is the master of Kung Fu Chess!"
        self.start_time = time.time()

    def overlay_message(self, img):
        """ מצייר את ההודעה על גבי התמונה אם הזמן לא עבר """
        if self.message and time.time() - self.start_time < self.duration:
            h, w = img.shape[:2]
            cv2.putText(img, self.message, (w//2 - 300, h//10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)
        elif self.message:
            self.message = None  # מחיקת ההודעה אחרי שהסתיימה
