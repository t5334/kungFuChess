# Announcer.py
import time
import cv2
from PubSub import PubSub


class Announcer:
    def __init__(self):
        self.message = None
        self.start_time = None
        self.duration = 3  # seconds
        PubSub.subscribe(self.show_start, "game_start")
        PubSub.subscribe(self.show_end, "game_over")

    def show_start(self, data):
        self.message = "🎮 המשחק התחיל!"
        self.start_time = time.time()

    def show_end(self, data):
        winner = data.get("winner", "לא ידוע")
        self.message = f"🏁 המשחק נגמר! המנצח: {winner}"
        self.start_time = time.time()

    def overlay_message(self, img):
        """ מצייר את ההודעה על גבי התמונה אם הזמן לא עבר """
        if self.message and time.time() - self.start_time < self.duration:
            h, w = img.shape[:2]
            cv2.putText(img, self.message, (w//2 - 300, h//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)
        elif self.message:
            self.message = None  # מחיקת ההודעה אחרי שהסתיימה
