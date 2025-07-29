import cv2

class UIOverlay:
    def __init__(self, logger, board_score):
        self.scoreboard = board_score
        self.logger = logger
        self.font = cv2.FONT_HERSHEY_SIMPLEX
    def draw_overlay(self, frame):
        white_moves = self.logger.get_moves("white")[-10:]
        black_moves = self.logger.get_moves("black")[-10:]
        white_pts = self.scoreboard.get_points("white")
        black_pts = self.scoreboard.get_points("black")

        # רקע לפאנל הלבן
        cv2.rectangle(frame, (0, 0), (200, 300), (50, 50, 50), -1)

        # פאנל הלבן (שמאל)
        x, y = 10, 30
        cv2.putText(frame, f"White Points: {white_pts}", (x, y + 220), self.font, 0.6, (255,255,255), 2)
        for i, move in enumerate(white_moves):
            cv2.putText(frame, move, (x, y + i*20), self.font, 0.5, (255,255,255), 1)
        
        # רקע לפאנל השחור
        x2 = frame.shape[1] - 200
        cv2.rectangle(frame, (x2, 0), (frame.shape[1], 300), (200, 200, 200), -1)

        # פאנל השחור (ימין)
        y2 = 30
        cv2.putText(frame, f"Black Points: {black_pts}", (x2 + 10, y2 + 220), self.font, 0.6, (0,0,0), 2)

        for i, move in enumerate(black_moves):
            cv2.putText(frame, move, (x2 + 10, y2 + i*20), self.font, 0.5, (0,0,0), 1)
        
        return frame

    # def draw_overlay(self, frame):
    #     white_moves = self.logger.get_moves("white")[-10:]
    #     black_moves = self.logger.get_moves("black")[-10:]
    #     white_pts = self.logger.get_points("white")
    #     black_pts = self.logger.get_points("black")


    #     # Draw white panel (left)
    #     x, y = 10, 30
    #     for i, move in enumerate(white_moves):
    #         cv2.putText(frame, move, (x, y + i*20), self.font, 0.5, (255,255,255), 1)
    #     cv2.putText(frame, f"White Points: {white_pts}", (x, y + 220), self.font, 0.6, (255,255,255), 2)

    #     # Draw black panel (right)
    #     x2, y2 = frame.shape[1] - 200, 30
    #     for i, move in enumerate(black_moves):
    #         cv2.putText(frame, move, (x2, y2 + i*20), self.font, 0.5, (0,0,0), 1)
    #     cv2.putText(frame, f"Black Points: {black_pts}", (x2, y2 + 220), self.font, 0.6, (0,0,0), 2)

    #     return frame
