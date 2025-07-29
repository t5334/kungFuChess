# Scoreboard.py
from PubSub import pubsub

class Scoreboard:
    def __init__(self):
        self.points = {"white": 0, "black": 0}
        self.value_map = {
            "P": 1,
            "N": 3,
            "B": 3,
            "R": 5,
            "Q": 9,
            "K": 0  # המלך לא שווה נקודות, סיום המשחק נעשה אחרת
        }

    def handle_capture(self, data):

       # attacer_id = data["attacker"]  # לדוגמה: "Pw2"
        captured_color = "white" if data["attacker_color"] == "w" else "black"
        capturing_color = "black" if captured_color == "white" else "white"

        # piece_type = attacer_id[0].upper()  # האות הראשונה מייצגת סוג כלי

        # value = self.value_map.get(piece_type, 0)
        # self.points[capturing_color] += value

        # print(f"[SCORE] to {attacer_id} {capturing_color} +{value} → {self.points[capturing_color]}")
        piece_type = data["piece_type"]  # כבר אות אחד: 'P', 'Q', וכו'

        value = self.value_map.get(piece_type.upper(), 0)
        self.points[capturing_color] += value

        print(f"[SCORE] {capturing_color} +{value} → {self.points[capturing_color]}")


    def get_points(self, color: str) -> int:
        return self.points[color]




# class ScoreBoard:
#     def __init__(self):
#         self.scores = {"W": 0, "B": 0}
#         self.piece_value = {
#             'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
#         }

#     def handle_capture(self, data):
#         victim_id = data['victim']
#         attacker_id = data['attacker']
#         victim_type = victim_id[0]  # P/N/B/... 
#         victim_color = victim_id[1]  # W/B
#         attacker_color = attacker_id[1]

#         value = self.piece_value.get(victim_type.upper(), 0)
#         self.scores[attacker_color] += value
#         print(f"[SCORE] {attacker_color} gets {value} points. Total: {self.scores}")
    
#     def get_score(self, color: str):
#         return self.scores.get(color.upper(), 0)