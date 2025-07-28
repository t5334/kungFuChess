class ScoreBoard:
    def __init__(self):
        self.score = {"W": 0, "B": 0}
        self.piece_value = {
            'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
        }

    def handle_capture(self, data):
        victim_id = data['victim']
        attacker_id = data['attacker']
        victim_type = victim_id[0]  # P/N/B/...
        victim_color = victim_id[1]  # W/B
        attacker_color = attacker_id[1]

        value = self.piece_value.get(victim_type.upper(), 0)
        self.score[attacker_color] += value
        print(f"[SCORE] {attacker_color} gets {value} points. Total: {self.score}")
