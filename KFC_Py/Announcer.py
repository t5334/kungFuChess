# Announcer.py
import time
import cv2
from PubSub import pubsub 


class Announcer:
    def __init__(self):
        self.message = None
        self.start_time = None
        self.duration = 3  # seconds
        
    def show_start(self, data):
        self.message = "welcome to Kung Fu Chess!"
        self.start_time = time.time()

    def show_end(self, data):
        winner = data.get("winner", "")
        path = f"../pieces/win{winner.lower()}.jpg"
        img = cv2.imread(path)

        if img is not None:
            resized = cv2.resize(img, (800, 800))
            cv2.imshow("Victory!", resized)
            cv2.waitKey(3000)
            cv2.destroyWindow("Victory!")
        else:
            print(f"Victory image not found: {path}")


    def overlay_message(self, img):
        """ מצייר את ההודעה על גבי התמונה אם הזמן לא עבר """
        if self.message and time.time() - self.start_time < self.duration:
            h, w = img.shape[:2]
            cv2.putText(img, self.message, (w//2 - 270, h//10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        elif self.message:
            self.message = None  # מחיקת ההודעה אחרי שהסתיימה
