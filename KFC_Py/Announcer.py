# Announcer.py
import time
import cv2
from PubSub import pubsub 


class Announcer:
    def __init__(self):
        self.message = None
        self.start_time = None
        self.duration = 3  # seconds
        self.victory_image = None
        self.victory_winner = None
        self.victory_start_time = None
        self.victory_duration = 5
        self.start_image = None
        self.start_image_time = None
        self.waiting_for_key = False
        
    def show_start(self, data):
        self.message = "welcome to Kung Fu Chess!"
        self.start_time = time.time()
        
        # טעינת תמונת הפתיחה
        start_path = "../pieces/start.jpg"
        start_img = cv2.imread(start_path)
        if start_img is not None:
            self.start_image = start_img
            self.start_image_time = time.time()
            # תמונת הפתיחה תוצג למשך 3 שניות בלבד, לא מחכה ללחיצה
            self.waiting_for_key = False
        else:
            print(f"Start image not found: {start_path}")

    def show_end(self, data):
        winner = data.get("winner", "")
        path = f"../pieces/win{winner.lower()}.jpg"
        img = cv2.imread(path)

        if img is not None:
            # שמור את תמונת הניצחון לשימוש מאוחר יותר על הלוח
            self.victory_image = img  # שמור בגודל המקורי
            self.victory_winner = winner
            self.victory_start_time = time.time()
            self.waiting_for_key = False  # לא מחכים ללחיצה, רק להצגה לפי זמן
        else:
            print(f"Victory image not found: {path}")
            self.victory_image = None


    def overlay_message(self, img):
        """ מצייר את ההודעה על גבי התמונה אם הזמן לא עבר """
        if self.message and time.time() - self.start_time < self.duration:
            h, w = img.shape[:2]
            cv2.putText(img, self.message, (w//2 - 270, h//10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        elif self.message:
            self.message = None  # מחיקת ההודעה אחרי שהסתיימה
        
        # הצגת תמונת הפתיחה על אזור הלוח (למשך זמן מוגבל)
        if (self.start_image is not None and 
            self.start_image_time is not None and 
            time.time() - self.start_image_time < 3):  # 3 שניות
            h, w = img.shape[:2]
            
            # הגדרת גבולות הלוח (בהנחה שהלוח במרכז)
            board_start_x = 384  # מיקום התחלת הלוח
            board_start_y = 104  # מיקום התחלת הלוח
            board_width = 512    # רוחב הלוח
            board_height = 512   # גובה הלוח
            
            # וידוא שהגבולות לא חורגים מהתמונה
            board_end_x = min(board_start_x + board_width, w)
            board_end_y = min(board_start_y + board_height, h)
            
            # שינוי גודל תמונת הפתיחה לגודל הלוח
            start_resized = cv2.resize(self.start_image, (board_end_x - board_start_x, board_end_y - board_start_y))
            
            # הצגת תמונת הפתיחה על אזור הלוח
            img[board_start_y:board_end_y, board_start_x:board_end_x] = start_resized
            
            # הוספת טקסט
            text = "Welcome to Kung Fu Chess!"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
            text_x = board_start_x + (board_width - text_size[0]) // 2
            text_y = board_end_y + 30
            
            cv2.putText(img, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        elif self.start_image is not None:
            # הזמן עבר, נמחק את תמונת הפתיחה
            self.start_image = None
            self.start_image_time = None
        
        # הצגת תמונת הניצחון על אזור הלוח (למשך 5 שניות)
        elif (self.victory_image is not None and 
              self.victory_start_time is not None and 
              time.time() - self.victory_start_time < 5):  # 5 שניות
            h, w = img.shape[:2]
            
            # הגדרת גבולות הלוח
            board_start_x = 384
            board_start_y = 104
            board_width = 512
            board_height = 512
            
            board_end_x = min(board_start_x + board_width, w)
            board_end_y = min(board_start_y + board_height, h)
            
            # שינוי גודל תמונת הניצחון לגודל הלוח
            victory_resized = cv2.resize(self.victory_image, (board_end_x - board_start_x, board_end_y - board_start_y))
            
            # הצגת תמונת הניצחון על אזור הלוח
            img[board_start_y:board_end_y, board_start_x:board_end_x] = victory_resized
            
            # הוספת טקסט
            winner_text = f"{self.victory_winner} Wins!"
            text_size = cv2.getTextSize(winner_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            text_x = board_start_x + (board_width - text_size[0]) // 2
            text_y = board_end_y + 40
            
            cv2.putText(img, winner_text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        elif self.victory_image is not None:
            # הזמן עבר, נמחק את תמונת הניצחון ונסיים את המשחק
            self.victory_image = None
            self.victory_start_time = None
    
    def handle_key_press(self):
        """נקרא כשלוחצים על מקש כלשהו - לא משמש יותר לתמונת הסיום"""
        return False
    
    def is_victory_screen_finished(self):
        """בדוק אם תמונת הסיום הסתיימה"""
        if (self.victory_image is not None and 
            self.victory_start_time is not None and 
            time.time() - self.victory_start_time >= 5):
            return True
        return False
